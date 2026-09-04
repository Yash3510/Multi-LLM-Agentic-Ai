import json
import tempfile
import unittest
from pathlib import Path

from sovereign_ai.agents import Ultron
from sovereign_ai.database import Database
from sovereign_ai.task_engine import TaskEngine


class Phase5Provider:
    def list_models(self): return ["local-test-model"]
    def generate(self, prompt, model):
        return "PASS\nVerified local result." if "ULTRON" in prompt else "Local analysis result"


class Phase5Tests(unittest.TestCase):
    def test_ultron_normalizes_structured_verification(self):
        result = Ultron(Phase5Provider()).validate(
            json.dumps({"status": "WARNING", "confidence": 0.61, "issues": ["Needs review"], "recommendation": "review"}),
            "local-test-model",
        )
        self.assertEqual(result["status"], "WARNING")
        self.assertFalse(result["passed"])
        self.assertEqual(result["confidence"], 0.61)
        self.assertEqual(result["recommendation"], "review")

    def test_human_review_decisions_are_persisted_and_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "phase5.db")
            try:
                engine = TaskEngine(db, Phase5Provider(), "fallback")
                task = engine.run("Analyze this report")
                self.assertEqual(task["status"], "awaiting_approval")
                self.assertEqual(db.execute("SELECT approval_state FROM tasks WHERE id=?", (task["task_id"],)).fetchone()[0], "pending")
                requested = engine.request_changes(task["task_id"], "Include the missing inspection date", "reviewer")
                self.assertEqual(requested["approval_state"], "changes_requested")
                with self.assertRaises(ValueError): engine.approve(task["task_id"], "reviewer")
                rejected = engine.reject(task["task_id"], "Evidence is insufficient", "reviewer")
                self.assertEqual(rejected["status"], "failed")
                actions = [row[0] for row in db.execute("SELECT action FROM audit_events WHERE username='reviewer'")]
                self.assertEqual(actions, ["task_changes_requested", "task_rejected"])
            finally:
                db.close()


if __name__ == "__main__": unittest.main()
