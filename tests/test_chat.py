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


if __name__ == "__main__": unittest.main()
