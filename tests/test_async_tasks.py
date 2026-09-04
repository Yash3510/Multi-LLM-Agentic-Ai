import tempfile
import time
import unittest
from pathlib import Path
from sovereign_ai.database import Database
from sovereign_ai.task_engine import TaskEngine
from sovereign_ai.task_manager import BackgroundTaskManager


class Provider:
    def list_models(self): return ["local-model"]
    def generate(self, prompt, model):
        if "ULTRON" in prompt: return "PASS\nValidated."
        return "Local analysis."


class AsyncTaskTests(unittest.TestCase):
    def test_submit_returns_before_background_execution_finishes(self):
        temp = tempfile.TemporaryDirectory()
        db = Database(Path(temp.name) / "tasks.db")
        manager = BackgroundTaskManager(TaskEngine(db, Provider(), "local-model"))
        started = time.monotonic()
        task_id = manager.submit("Analyze a local task")
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.5)
        for _ in range(40):
            row = db.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row and row["status"] in ("awaiting_approval", "failed"):
                break
            time.sleep(0.05)
        self.assertEqual(db.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()["status"], "awaiting_approval")
        manager.shutdown(); db.close(); temp.cleanup()


if __name__ == "__main__": unittest.main()
