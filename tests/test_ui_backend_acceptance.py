import os
import tempfile
import unittest
from pathlib import Path


class TkinterBackendAcceptanceTests(unittest.TestCase):
    def test_tkinter_can_attach_to_live_backend(self):
        backend_url = os.getenv("SOVEREIGN_BACKEND_URL", "http://localhost:8000")
        try:
            import tkinter as tk
            from sovereign_ai.backend_client import BackendClient
            from sovereign_ai.config import Settings
            from sovereign_ai.database import Database
            from sovereign_ai.local_provider import OpenAICompatibleProvider
            from sovereign_ai.ui import SovereignApp
            client = BackendClient(backend_url)
            health = client.health()
            self.assertTrue(health["Backend"][0], health)
            username, password = "phase1_admin", "phase1_password"
            try:
                client.setup(username, password)
            except RuntimeError:
                pass
            client.login(username, password)
            models = client.models()
            self.assertTrue(models)
            conversation_id = client.create_conversation("Phase 1 live UI test", models[0])
            queued = client.submit_task("Reply with a short local test confirmation", models[0], conversation_id)
            self.assertEqual(queued["status"], "queued")
        except Exception as exc:
            self.skipTest(f"live Tkinter backend unavailable: {exc}")

        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        settings = Settings(root, root / "db.sqlite", root / "files", "http://127.0.0.1:1234/v1", "qwen/qwen3.5-9b")
        db = Database(settings.db_path)
        app = None
        try:
            app = SovereignApp(db, OpenAICompatibleProvider(settings.local_model_url), settings, backend=client)
            app.withdraw()
            app.show_main()
            self.assertIsNotNone(app.model_box)
            self.assertTrue(app.backend.token)
            app.update_idletasks()
        finally:
            if app:
                app.destroy()
            db.close()
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
