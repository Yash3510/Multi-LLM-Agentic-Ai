import base64
import json
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path
from sovereign_ai.api import ApiServer
from sovereign_ai.config import Settings
from sovereign_ai.database import Database


class FakeProvider:
    def list_models(self):
        return ["test-model"]

    def generate(self, prompt, model):
        return "PASS\nLocal verification completed." if "ULTRON" in prompt else "Local analysis result"

    def health_check(self):
        return True, "fake local provider"


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.settings = Settings(root, root / "db.sqlite", root / "files", "http://127.0.0.1:9/v1", "test-model")
        self.db = Database(self.settings.db_path)
        self.server = ApiServer("127.0.0.1", 0, self.db, FakeProvider(), self.settings)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.conn = HTTPConnection("127.0.0.1", self.server.httpd.server_address[1])

    def tearDown(self):
        self.server.shutdown(); self.db.close(); self.temp.cleanup()

    def request(self, method, path, payload=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token: headers["Authorization"] = "Bearer " + token
        body = json.dumps(payload).encode() if payload is not None else None
        self.conn.request(method, path, body, headers)
        response = self.conn.getresponse()
        return response.status, json.loads(response.read())

    def test_setup_login_protected_route_and_file_upload(self):
        status, _ = self.request("GET", "/api/conversations")
        self.assertEqual(status, 401)
        self.assertEqual(self.request("POST", "/api/setup", {"username": "admin", "password": "strongpass"})[0], 201)
        status, login = self.request("POST", "/api/login", {"username": "admin", "password": "strongpass"})
        self.assertEqual(status, 200)
        token = login["token"]
        status, created = self.request("POST", "/api/conversations", {"title": "Test", "model": "test-model"}, token)
        self.assertEqual(status, 201)
        content = base64.b64encode(b"hello").decode()
        self.assertEqual(self.request("POST", "/api/files", {"name": "test.txt", "content": content}, token)[0], 201)
        self.assertEqual(self.request("POST", "/api/logout", token=token)[0], 200)
        self.assertEqual(self.request("GET", "/api/conversations")[0], 401)

    def test_task_api_is_async_and_exposes_status(self):
        self.assertEqual(self.request("POST", "/api/setup", {"username": "admin", "password": "strongpass"})[0], 201)
        token = self.request("POST", "/api/login", {"username": "admin", "password": "strongpass"})[1]["token"]
        status, task = self.request("POST", "/api/tasks", {"request": "Analyze this local test task"}, token)
        self.assertEqual(status, 202)
        self.assertEqual(task["status"], "queued")
        task_id = task["task_id"]
        deadline = time.time() + 3
        current = None
        while time.time() < deadline:
            status, current = self.request("GET", f"/api/tasks/{task_id}", token=token)
            self.assertIn("status", current, current)
            if current["status"] in {"awaiting_approval", "completed", "failed"}:
                break
            time.sleep(0.02)
        self.assertEqual(status, 200)
        self.assertEqual(current["status"], "awaiting_approval")
        status, tasks = self.request("GET", "/api/tasks", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == task_id for item in tasks))
        status, approved = self.request("POST", f"/api/tasks/{task_id}/approve", {}, token)
        self.assertEqual(status, 200)
        self.assertEqual(approved["status"], "completed")


if __name__ == "__main__": unittest.main()
