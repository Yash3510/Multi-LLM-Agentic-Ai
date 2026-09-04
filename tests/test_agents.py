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
        self.assertEqual(result["status"], "complete")
        self.assertEqual([row["agent"] for row in self.db.execute("SELECT * FROM task_steps ORDER BY step_number")], ["friday", "jarvis", "ultron"])
        self.assertTrue(any(event["message"] == "Final result ready" for event in events))

    def test_ultron_gets_one_retry_then_completes(self):
        events = []
        provider = FakeProvider(["FAIL\nContradiction found.", "PASS\nResolved."])
        result = TaskEngine(self.db, provider, "fallback").run("Analyze this report", on_event=events.append)
        self.assertEqual(result["status"], "complete")
        self.assertTrue(any(event["status"] == "retrying" for event in events))

    def test_repeated_ultron_failure_is_recorded(self):
        result = TaskEngine(self.db, FakeProvider(["FAIL\nIssue.", "FAIL\nStill issue."]), "fallback").run("Analyze this report")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.db.execute("SELECT status FROM tasks WHERE id=?", (result["task_id"],)).fetchone()[0], "failed")


if __name__ == "__main__": unittest.main()
