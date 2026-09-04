import base64
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from sovereign_ai.api import ApiServer
from sovereign_ai.config import Settings
from sovereign_ai.database import Database
from sovereign_ai.local_provider import OpenAICompatibleProvider


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.settings = Settings(root, root / "db.sqlite", root / "files", "http://127.0.0.1:9/v1", "test-model")
        self.db = Database(self.settings.db_path)
        self.server = ApiServer("127.0.0.1", 0, self.db, OpenAICompatibleProvider(self.settings.local_model_url), self.settings)
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


if __name__ == "__main__": unittest.main()
