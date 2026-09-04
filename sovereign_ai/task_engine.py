import json
import logging
from datetime import datetime
from .agents import agents_for
from .router import ModelRouter


class TaskEngine:
    def __init__(self, db, provider, default_model):
        self.db, self.provider = db, provider
        self.router = ModelRouter(provider, default_model)
        self.agents = agents_for(provider)
        self.logger = logging.getLogger("sovereign_ai.tasks")

    def plan(self, request: str, model: str | None = None) -> dict:
        plan = self.agents["tony"].plan(request)
        selected = self.router.route(plan["task_type"], model)
        for step in plan["steps"]:
            step["model"] = selected
        return plan

    def run(self, request: str, conversation_id: int | None = None,
            user_name: str = "local-user", model: str | None = None, on_event=None) -> dict:
        plan = self.plan(request, model)
        task_row = self.db.execute(
            "INSERT INTO tasks(conversation_id,user_name,status,plan_json,input,model,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (conversation_id, user_name, "running", json.dumps(plan), request, plan["steps"][0]["model"]),
        )
        task_id = task_row.lastrowid
        self._event(on_event, task_id, "tony", "Task understood", "complete")
        self._event(on_event, task_id, "tony", "Plan created", "complete")
        payload = request
        final = ""
        verification = {}
        verification_retries = 0
        for index, step in enumerate(plan["steps"], 1):
            agent_name, action, selected_model = step["agent"], step["action"], step["model"]
            self.db.execute("INSERT INTO task_steps(task_id,step_number,agent,action,model,status,input,started_at) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                            (task_id, index, agent_name, action, selected_model, "running", payload))
            step_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.db.execute("UPDATE tasks SET current_step=?,agent=?,model=? WHERE id=?", (index, agent_name, selected_model, task_id))
            self._event(on_event, task_id, agent_name, "Running " + action, "running")
            agent = self.agents[agent_name]
            try:
                result = agent.execute(action, payload, selected_model)
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
                        self.db.execute("UPDATE tasks SET status='replanning',verification=?,output=? WHERE id=?", (json.dumps(validation), result, task_id))
                        self._event(on_event, task_id, agent_name, "Challenge failed; task requires replan", "failed")
                        raise RuntimeError("ULTRON rejected the result: " + result[:300])
                self.db.execute("UPDATE task_steps SET status='complete',output=?,verification=?,completed_at=CURRENT_TIMESTAMP WHERE id=?",
                                (result, json.dumps(validation), step_id))
                self._event(on_event, task_id, agent_name, "Completed", "complete")
                payload, final, verification = result, result, validation
            except Exception as exc:
                self.logger.exception("Task %s failed at %s", task_id, agent_name)
                self.db.execute("UPDATE task_steps SET status='failed',error=?,completed_at=CURRENT_TIMESTAMP WHERE id=?", (str(exc), step_id))
                self.db.execute("UPDATE tasks SET status='failed',output=?,verification=? WHERE id=?", (str(exc), json.dumps(verification), task_id))
                self._event(on_event, task_id, agent_name, str(exc), "failed")
                return {"task_id": task_id, "status": "failed", "plan": plan, "result": str(exc), "verification": verification}
        self.db.execute("UPDATE tasks SET status='complete',output=?,verification=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (final, json.dumps(verification), task_id))
        self._event(on_event, task_id, "ultron", "Final result ready", "complete")
        return {"task_id": task_id, "status": "complete", "plan": plan, "result": final, "verification": verification}

    def _event(self, callback, task_id, agent, message, status):
        if callback:
            callback({"task_id": task_id, "agent": agent, "message": message, "status": status})
