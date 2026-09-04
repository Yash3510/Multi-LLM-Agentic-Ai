import json
import logging
from datetime import datetime
from .agents import agents_for
from .router import ModelRouter
from .tools import ToolRegistry
from .workflow import AgenticWorkflow


class TaskEngine:
    def __init__(self, db, provider, default_model, file_service=None, knowledge=None):
        self.db, self.provider = db, provider
        self.router = ModelRouter(provider, default_model)
        self.tools = ToolRegistry(file_service, db=db)
        self.agents = agents_for(provider, self.tools, knowledge)
        workspace = (file_service.storage_dir / "artifacts") if file_service else self.tools.workspace / "artifacts"
        self.coding_workflow = AgenticWorkflow(provider, self.tools, workspace)
        self.logger = logging.getLogger("sovereign_ai.tasks")

    def plan(self, request: str, model: str | None = None) -> dict:
        plan = self.agents["tony"].plan(request)
        selected = self.router.route(plan["task_type"], model)
        for step in plan["steps"]:
            step["model"] = selected
        return plan

    def create_task(self, request: str, user_name: str = "local-user", model: str | None = None, conversation_id=None):
        plan = self.plan(request, model)
        row = self.db.execute(
            "INSERT INTO tasks(conversation_id,user_name,status,plan_json,input,model,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (conversation_id, user_name, "queued", json.dumps(plan), request, plan["steps"][0]["model"]),
        )
        return row.lastrowid

    def run(self, request: str, conversation_id: int | None = None,
            user_name: str = "local-user", model: str | None = None, on_event=None, task_id=None) -> dict:
        if not task_id and self.plan(request, model)["task_type"] == "code":
            return self.run_coding_workflow(request, conversation_id, user_name, model, on_event)
        if task_id:
            row = self.db.execute("SELECT plan_json FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                raise ValueError("Task not found")
            plan = json.loads(row["plan_json"])
            if plan.get("task_type") == "code":
                return self.run_coding_workflow(request, conversation_id, user_name, model, on_event, task_id, plan)
            self.db.execute("UPDATE tasks SET status='planning',updated_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))
        else:
            plan = self.plan(request, model)
            task_row = self.db.execute(
                "INSERT INTO tasks(conversation_id,user_name,status,plan_json,input,model,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                (conversation_id, user_name, "planning", json.dumps(plan), request, plan["steps"][0]["model"]),
            )
            task_id = task_row.lastrowid
        self._event(on_event, task_id, "tony", "Task understood", "complete")
        self._event(on_event, task_id, "tony", "Plan created", "complete")
        self.db.execute("UPDATE tasks SET status='routing',updated_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))
        payload = request
        final = ""
        verification = {}
        verification_retries = 0
        replan_attempts = 0
        step_index = 0
        steps = plan["steps"]
        while step_index < len(steps):
            index, step = step_index + 1, steps[step_index]
            agent_name, action, selected_model = step["agent"], step["action"], step["model"]
            if agent_name == "ultron":
                verification_retries = 0
            self.db.execute("INSERT INTO task_steps(task_id,step_number,agent,action,model,status,input,started_at) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                            (task_id, index, agent_name, action, selected_model, "running", payload))
            step_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.db.execute("UPDATE tasks SET current_step=?,agent=?,model=? WHERE id=?", (index, agent_name, selected_model, task_id))
            self.db.execute("UPDATE tasks SET status=? WHERE id=?", ("verifying" if agent_name == "ultron" else "executing", task_id))
            self._event(on_event, task_id, agent_name, "Running " + action, "running")
            agent = self.agents[agent_name]
            try:
                agent_payload = request + "\n\nAnalysis context:\n" + payload if agent_name == "jarvis" else payload
                result = agent.execute(action, agent_payload, selected_model)
                validation = agent.validate(result, selected_model)
                if agent_name == "ultron" and not validation["passed"]:
                    if verification_retries < 1:
                        verification_retries += 1
                        self._event(on_event, task_id, agent_name, "Challenge failed; retrying verification", "retrying")
                        result = agent.execute(action, payload, selected_model)
                        validation = agent.validate(result, selected_model)
                    if validation["passed"]:
                        self._event(on_event, task_id, agent_name, "Retry passed", "complete")
                    else:
                        self.db.execute("UPDATE task_steps SET status='failed',output=?,verification=?,error=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",
                                        (result, json.dumps(validation), "Verification challenge failed", step_id))
                        if replan_attempts < 1:
                            replan_attempts += 1
                            replan = self.agents["tony"].replan(request, result, selected_model)
                            steps.extend(replan["steps"])
                            self.db.execute("UPDATE tasks SET status='replanning',plan_json=?,verification=?,output=? WHERE id=?", (json.dumps({**plan, "replan": replan}), json.dumps(validation), result, task_id))
                            self._event(on_event, task_id, "tony", "Replanned after ULTRON challenge", "replanning")
                            payload = request + "\n\nPrevious challenge:\n" + result
                            step_index += 1
                            continue
                        self.db.execute("UPDATE tasks SET status='failed',verification=?,output=? WHERE id=?", (json.dumps(validation), result, task_id))
                        self._event(on_event, task_id, agent_name, "Challenge failed after replan", "failed")
                        raise RuntimeError("ULTRON rejected the result after replan: " + result[:300])
                self.db.execute("UPDATE task_steps SET status='complete',output=?,verification=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",
                                (result, json.dumps(validation), step_id))
                self._event(on_event, task_id, agent_name, "Completed", "complete")
                payload, final, verification = result, result, validation
                step_index += 1
            except Exception as exc:
                self.logger.exception("Task %s failed at %s", task_id, agent_name)
                self.db.execute("UPDATE task_steps SET status='failed',error=?,completed_at=CURRENT_TIMESTAMP WHERE id=?", (str(exc), step_id))
                self.db.execute("UPDATE tasks SET status='failed',output=?,verification=? WHERE id=?", (str(exc), json.dumps(verification), task_id))
                self._event(on_event, task_id, agent_name, str(exc), "failed")
                return {"task_id": task_id, "status": "failed", "plan": plan, "result": str(exc), "verification": verification}
        self.db.execute("UPDATE tasks SET status='awaiting_approval',output=?,verification=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (final, json.dumps(verification), task_id))
        self._event(on_event, task_id, "ultron", "Final result awaiting human approval", "awaiting_approval")
        return {"task_id": task_id, "status": "awaiting_approval", "plan": plan, "result": final, "verification": verification}

    def run_coding_workflow(self, request, conversation_id=None, user_name="local-user", model=None, on_event=None, task_id=None, plan=None, approved=False):
        plan = plan or self.plan(request, model)
        if task_id is None:
            row = self.db.execute("INSERT INTO tasks(conversation_id,user_name,status,plan_json,input,model,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                                  (conversation_id, user_name, "planning", json.dumps(plan), request, plan["steps"][0]["model"]))
            task_id = row.lastrowid
        state = self.coding_workflow.run(request, model or plan["steps"][0]["model"], task_id, approved)
        status = {"awaiting_approval": "awaiting_approval", "completed": "completed", "failed": "failed"}.get(state.get("final_status"), "failed")
        output = json.dumps(state.get("tool_result") or state.get("verification_result") or {})
        self.db.execute("UPDATE tasks SET status=?,agent=?,current_step=?,output=?,plan_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (status, state.get("current_agent"), 0, output, json.dumps({"task_type": "code", "workflow_state": state}), task_id))
        if on_event:
            on_event({"task_id": task_id, "agent": state.get("current_agent", "tony"), "message": state.get("current_step", status), "status": status})
        return {"task_id": task_id, "status": status, "result": output, "verification": state.get("verification_result", {}), "workflow_state": state}

    def approve(self, task_id: int, user_name: str = "local-user") -> dict:
        row = self.db.execute("SELECT status,output FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise ValueError("Task not found")
        if row["status"] != "awaiting_approval":
            raise ValueError("Task is not awaiting approval")
        plan_row = self.db.execute("SELECT plan_json,input,model FROM tasks WHERE id=?", (task_id,)).fetchone()
        if plan_row and plan_row["plan_json"] and "workflow_state" in plan_row["plan_json"]:
            state = json.loads(plan_row["plan_json"])["workflow_state"]
            result = self.run_coding_workflow(plan_row["input"], user_name=user_name, model=plan_row["model"], task_id=task_id, approved=True)
            if result["status"] != "completed": raise ValueError("Approved coding workflow did not complete")
            self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", (user_name, "task_approved", f"Task {task_id} approved"))
            return {"task_id": task_id, "status": "completed", "result": result["result"]}
        self.db.execute("UPDATE tasks SET status='completed',updated_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))
        self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", (user_name, "task_approved", f"Task {task_id} approved"))
        return {"task_id": task_id, "status": "completed", "result": row["output"]}

    def _event(self, callback, task_id, agent, message, status):
        if callback:
            callback({"task_id": task_id, "agent": agent, "message": message, "status": status})
