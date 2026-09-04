import tempfile
import unittest
from pathlib import Path

from sovereign_ai.database import Database
from sovereign_ai.tools import ToolRegistry
from sovereign_ai.workflow import AgenticWorkflow


class CodingProvider:
    def generate(self, prompt, model):
        return "import csv\nrows = list(csv.DictReader(open('/workspace/input.csv')))\nhours = [float(row['hours']) for row in rows]\nprint(f'TOTAL={sum(hours):g}')\nprint(f'AVERAGE={sum(hours) / len(hours):g}')"


class WorkflowTests(unittest.TestCase):
    def test_high_risk_tool_pauses_until_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            try:
                workflow = AgenticWorkflow(CodingProvider(), ToolRegistry(db=db, workspace=Path(directory) / "workspace"), Path(directory) / "artifacts")
                state = workflow.run("Create a Python program that calculates total and average employee hours", "local-coding-model", "approval", approved=False)
                self.assertEqual(state["final_status"], "awaiting_approval")
                self.assertTrue(state["approval_required"])
                self.assertFalse(state.get("tool_result"))
            finally:
                db.close()

    def test_coding_workflow_executes_in_sandbox_and_ultron_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            try:
                workflow = AgenticWorkflow(CodingProvider(), ToolRegistry(db=db, workspace=Path(directory) / "workspace"), Path(directory) / "artifacts")
                state = workflow.run("Create a Python program that calculates total and average employee hours", "local-coding-model", "coding", approved=True)
                self.assertEqual(state["final_status"], "completed")
                self.assertEqual(state["verification_result"]["status"], "PASS")
                self.assertIn("TOTAL=14", state["tool_result"]["result"]["stdout"])
                self.assertTrue(any(item["file_path"].endswith("solution.py") for item in state["artifacts"]))
            finally:
                db.close()


if __name__ == "__main__": unittest.main()
