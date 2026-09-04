import tempfile
import unittest
from pathlib import Path
from sovereign_ai.config import Settings
from sovereign_ai.database import Database
from sovereign_ai.health import check
from sovereign_ai.local_provider import OpenAICompatibleProvider


class Phase6Tests(unittest.TestCase):
    def test_external_model_endpoint_is_rejected_and_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "security.db")
            try:
                with self.assertRaises(ValueError): OpenAICompatibleProvider("https://api.example.com/v1", True, db)
                event = db.execute("SELECT action,details FROM audit_events WHERE action='security_blocked'").fetchone()
                self.assertEqual(event[0], "security_blocked")
                self.assertNotIn("secret", event[1].lower())
            finally: db.close()

    def test_health_exposes_enforced_security_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); db = Database(root / "security.db")
            settings = Settings(root, root / "db.sqlite", root / "files", "http://127.0.0.1:1234/v1", "local-model")
            class Provider:
                def health_check(self): return False, "offline"
            statuses = check(db, Provider(), settings.storage_dir, settings)
            self.assertEqual(statuses["External APIs"][0], True)
            self.assertIn("Security events", statuses)
            db.close()


if __name__ == "__main__": unittest.main()
