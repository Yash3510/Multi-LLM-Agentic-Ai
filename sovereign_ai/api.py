import base64
import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class ApiServer:
    def __init__(self, host, port, db, provider, settings):
        from .auth import AuthService
        from .conversations import ConversationService
        from .files import FileService
        from .health import check
        self.db, self.provider, self.settings = db, provider, settings
        self.auth, self.conversations = AuthService(db), ConversationService(db)
        self.files, self.health = FileService(db, settings.storage_dir), check
        self.logger = logging.getLogger("sovereign_ai.api")
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                server.logger.info("%s %s", self.command, fmt % args)

            def send_json(self, status, payload):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def read_json(self):
                length = int(self.headers.get("Content-Length", 0))
                if length > 10 * 1024 * 1024:
                    raise ValueError("Request is too large")
                return json.loads(self.rfile.read(length) or b"{}")

            def user(self):
                header = self.headers.get("Authorization", "")
                token = header.removeprefix("Bearer ").strip()
                return server.auth.session_user(token), token

            def do_GET(self):
                path = urlparse(self.path).path.rstrip("/")
                if path == "/api/health":
                    return self.send_json(200, server.health(server.db, server.provider, server.settings.storage_dir))
                username, _ = self.user()
                if not username:
                    return self.send_json(401, {"error": "Authentication required"})
                if path == "/api/conversations":
                    return self.send_json(200, [dict(row) for row in server.conversations.list()])
                if path == "/api/models":
                    return self.send_json(200, {"models": list(server.provider.list_models())})
                if path == "/api/files":
                    return self.send_json(200, [dict(row) for row in server.files.list_files()])
                if path.startswith("/api/conversations/") and path.endswith("/messages"):
                    conversation_id = path.split("/")[3]
                    return self.send_json(200, [dict(row) for row in server.conversations.messages(int(conversation_id))])
                return self.send_json(404, {"error": "Route not found"})

            def do_POST(self):
                path = urlparse(self.path).path.rstrip("/")
                try:
                    payload = self.read_json()
                    if path == "/api/setup":
                        server.auth.create_admin(payload.get("username", ""), payload.get("password", ""))
                        return self.send_json(201, {"created": True})
                    if path == "/api/login":
                        token = server.auth.create_session(payload.get("username", ""), payload.get("password", ""))
                        return self.send_json(200, {"token": token})
                    username, token = self.user()
                    if not username:
                        return self.send_json(401, {"error": "Authentication required"})
                    if path == "/api/logout":
                        server.auth.logout(token)
                        return self.send_json(200, {"logged_out": True})
                    if path == "/api/conversations":
                        conversation_id = server.conversations.create(payload.get("title", "New conversation"), payload.get("model", server.settings.default_model))
                        return self.send_json(201, {"id": conversation_id})
                    if path.startswith("/api/conversations/") and path.endswith("/chat"):
                        conversation_id = int(path.split("/")[3])
                        prompt = payload["content"].strip()
                        model = payload.get("model", server.settings.default_model)
                        server.conversations.add_message(conversation_id, "user", prompt)
                        messages = [dict(row) for row in server.conversations.messages(conversation_id)]
                        answer = server.provider.chat(messages, model)
                        server.conversations.add_message(conversation_id, "assistant", answer)
                        return self.send_json(200, {"role": "assistant", "content": answer})
                    if path == "/api/files":
                        name = payload.get("name", "upload.txt")
                        raw = base64.b64decode(payload.get("content", ""), validate=True)
                        temp = server.settings.data_dir / (".upload_" + name.replace("\\", "_").replace("/", "_"))
                        temp.write_bytes(raw)
                        try:
                            return self.send_json(201, server.files.store(str(temp)))
                        finally:
                            temp.unlink(missing_ok=True)
                    if path.startswith("/api/conversations/") and path.endswith("/messages"):
                        conversation_id = int(path.split("/")[3])
                        server.conversations.add_message(conversation_id, payload["role"], payload["content"])
                        return self.send_json(201, {"created": True})
                    return self.send_json(404, {"error": "Route not found"})
                except (ValueError, KeyError, FileNotFoundError) as exc:
                    return self.send_json(400, {"error": str(exc)})
                except Exception:
                    server.logger.exception("API request failed")
                    return self.send_json(500, {"error": "Internal server error"})

            def do_DELETE(self):
                path = urlparse(self.path).path.rstrip("/")
                username, _ = self.user()
                if not username:
                    return self.send_json(401, {"error": "Authentication required"})
                if path.startswith("/api/files/"):
                    server.files.delete(int(path.split("/")[-1]))
                    return self.send_json(200, {"deleted": True})
                return self.send_json(404, {"error": "Route not found"})

        self.httpd = ThreadingHTTPServer((host, port), Handler)

    def serve_forever(self):
        self.logger.info("API server listening on %s", self.httpd.server_address)
        self.httpd.serve_forever()

    def shutdown(self):
        self.httpd.shutdown()
