import tempfile
import unittest
from pathlib import Path
from sovereign_ai.database import Database
from sovereign_ai.task_engine import TaskEngine


class FakeProvider:
    def __init__(self, verification_answers=None):
        self.verification_answers = iter(verification_answers or ["PASS\nNo concerns."])

    def list_models(self):
        return ["local-analysis-model"]

    def generate(self, prompt, model):
        if "ULTRON" in prompt:
            return next(self.verification_answers)
        return "FRIDAY findings: request analyzed."


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "runtime.db")

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_agents_execute_in_order_and_persist_task(self):
        events = []
        result = TaskEngine(self.db, FakeProvider(), "fallback").run("Analyze this report", on_event=events.append)
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual([row["agent"] for row in self.db.execute("SELECT * FROM task_steps ORDER BY step_number")], ["friday", "jarvis", "ultron"])
        self.assertTrue(any(event["message"] == "Final result awaiting human approval" for event in events))

    def test_ultron_gets_one_retry_then_completes(self):
        events = []
        provider = FakeProvider(["FAIL\nContradiction found.", "PASS\nResolved."])
        result = TaskEngine(self.db, provider, "fallback").run("Analyze this report", on_event=events.append)
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertTrue(any(event["status"] == "retrying" for event in events))

    def test_repeated_ultron_failure_is_recorded(self):
        result = TaskEngine(self.db, FakeProvider(["FAIL\nIssue.", "FAIL\nStill issue.", "FAIL\nReplan issue.", "FAIL\nReplan still failed."]), "fallback").run("Analyze this report")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.db.execute("SELECT status FROM tasks WHERE id=?", (result["task_id"],)).fetchone()[0], "failed")

    def test_failed_verification_triggers_tony_replan(self):
        provider = FakeProvider(["FAIL\nIssue.", "FAIL\nStill issue.", "PASS\nReplanned."])
        events = []
        result = TaskEngine(self.db, provider, "fallback").run("Analyze this report", on_event=events.append)
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertTrue(any(event["message"] == "Replanned after ULTRON challenge" for event in events))

    def test_human_approval_changes_task_state(self):
        result = TaskEngine(self.db, FakeProvider(), "fallback").run("Calculate 2 + 2")
        self.assertEqual(result["status"], "awaiting_approval")
        jarvis_output = self.db.execute("SELECT output FROM task_steps WHERE task_id=? AND agent='jarvis'", (result["task_id"],)).fetchone()[0]
        self.assertIn("Calculator result: 4", jarvis_output)
        approved = TaskEngine(self.db, FakeProvider(), "fallback").approve(result["task_id"], "admin")
        self.assertEqual(approved["status"], "completed")


if __name__ == "__main__": unittest.main()
