from typing import TypedDict
from pathlib import Path

from .deliverables import DeliverableService


class WorkflowState(TypedDict, total=False):
    task_id: str
    user_request: str
    current_agent: str
    selected_model: str
    current_step: str
    tool_name: str
    tool_input: dict
    tool_result: dict
    artifacts: list
    verification_result: dict
    approval_required: bool
    approval_status: str
    retry_count: int
    errors: list
    final_status: str
    generated_code: str
    approved: bool


class AgenticWorkflow:
    """LangGraph workflow used for bounded coding/tool execution."""

    MAX_RETRIES = 2

    def __init__(self, provider, tools, workspace):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as exc:
            raise RuntimeError("LangGraph is required for agentic workflows") from exc
        self.END, self.graph_type = END, StateGraph
        self.provider, self.tools = provider, tools
        self.deliverables = DeliverableService(workspace)
        graph = StateGraph(WorkflowState)
        graph.add_node("tony", self._tony)
        graph.add_node("jarvis_generate", self._jarvis_generate)
        graph.add_node("jarvis_execute", self._jarvis_execute)
        graph.add_node("ultron", self._ultron)
        graph.add_edge(START, "tony")
        graph.add_edge("tony", "jarvis_generate")
        graph.add_edge("jarvis_generate", "jarvis_execute")
        graph.add_conditional_edges("jarvis_execute", self._after_execute, {"ultron": "ultron", END: END})
        graph.add_conditional_edges("ultron", self._after_ultron, {"retry": "jarvis_generate", END: END})
        self.graph = graph.compile()

    def run(self, request, model, task_id="workflow", approved=False):
        state: WorkflowState = {"task_id": str(task_id), "user_request": request, "selected_model": model,
                                "tool_name": "execute_python", "tool_input": {}, "artifacts": [],
                                "errors": [], "retry_count": 0, "approval_status": "not_required",
                                "approval_required": False, "final_status": "queued", "approved": approved}
        return self.graph.invoke(state)

    def _tony(self, state):
        return {"current_agent": "tony", "current_step": "planning", "final_status": "routing"}

    def _jarvis_generate(self, state):
        prompt = ("You are JARVIS. Generate only Python code, without markdown fences, for this safe local task. "
                  "The program must read /workspace/input.csv and print TOTAL=<number> and AVERAGE=<number>. "
                  "Do not use network, subprocess, or filesystem paths outside /workspace.\n\nTASK: " + state["user_request"])
        if state.get("errors"):
            prompt += "\nCorrect the previous execution failure: " + state["errors"][-1]
        code = self.provider.generate(prompt, state["selected_model"]).strip()
        if "```" in code:
            code = code.replace("```python", "").replace("```", "").strip()
        artifact = self.deliverables.text(f"{state['task_id']}/solution.py", code, state["task_id"])
        input_csv = "employee,hours\nAlice,8\nBob,6\n"
        input_artifact = self.deliverables.csv(f"{state['task_id']}/input.csv", ["employee", "hours"], [["Alice", 8], ["Bob", 6]], state["task_id"])
        return {"current_agent": "jarvis", "current_step": "code_generated", "generated_code": code, "artifacts": state.get("artifacts", []) + [artifact, input_artifact], "tool_input": {"code": code, "files": {"input.csv": input_csv}}}

    def _jarvis_execute(self, state):
        if not state.get("approved"):
            return {"current_agent": "jarvis", "current_step": "approval_required", "approval_required": True, "approval_status": "pending", "final_status": "awaiting_approval"}
        result = self.tools.execute_tool("execute_python", state["tool_input"], permission="execute", approved=True, task_id=state["task_id"])
        return {"current_agent": "jarvis", "current_step": "sandbox_executed", "tool_result": result, "approval_status": "approved"}

    def _after_execute(self, state):
        return "ultron" if state.get("tool_result") else self.END

    def _ultron(self, state):
        result = state["tool_result"]
        output = result.get("result", {}) if result.get("success") else result
        stdout = output.get("stdout", "") if isinstance(output, dict) else ""
        passed = bool(result.get("success") and result.get("result", {}).get("exit_code") == 0 and "TOTAL=" in stdout and "AVERAGE=" in stdout)
        verification = {"status": "PASS" if passed else "FAIL", "issues": [] if passed else [result.get("error") or "Expected TOTAL and AVERAGE output was not produced"], "retry_required": not passed and state.get("retry_count", 0) < self.MAX_RETRIES}
        if passed:
            return {"current_agent": "ultron", "current_step": "verified", "verification_result": verification, "final_status": "completed"}
        return {"current_agent": "ultron", "current_step": "retrying", "verification_result": verification, "final_status": "retrying", "retry_count": state.get("retry_count", 0) + 1, "errors": state.get("errors", []) + verification["issues"]}

    def _after_ultron(self, state):
        return "retry" if state.get("verification_result", {}).get("retry_required") else self.END
