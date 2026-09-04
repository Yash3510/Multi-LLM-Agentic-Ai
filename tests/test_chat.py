import tempfile
import unittest
from pathlib import Path
from sovereign_ai.database import Database
from sovereign_ai.task_engine import TaskEngine


class ChatProvider:
    def list_models(self): return ["local-chat-model"]
    def generate(self, prompt, model): return "Hello from Tony."


class ChatTests(unittest.TestCase):
    def test_normal_chat_uses_local_model_and_completes(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "chat.db")
            result = TaskEngine(db, ChatProvider(), "fallback").chat("Hello Tony")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["result"], "Hello from Tony.")
            self.assertEqual(db.execute("SELECT status FROM tasks WHERE id=?", (result["task_id"],)).fetchone()[0], "completed")
            db.close()

    def test_explicit_file_request_uses_safe_registered_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "chat.db")
            engine = TaskEngine(db, ChatProvider(), "fallback", knowledge=None)
            engine.tools.workspace = Path(directory).resolve()
            result = engine.chat("Create a file named report.txt")
            self.assertEqual(result["status"], "completed")
            self.assertTrue((Path(directory) / "report.txt").exists())
            db.close()


if __name__ == "__main__": unittest.main()
