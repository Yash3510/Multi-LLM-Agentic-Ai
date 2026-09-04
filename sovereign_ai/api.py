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
        from .task_engine import TaskEngine
        from .knowledge import KnowledgeService
        from .task_manager import BackgroundTaskManager
        self.db, self.provider, self.settings = db, provider, settings
        self.auth, self.conversations = AuthService(db), ConversationService(db)
        self.files, self.health = FileService(db, settings.storage_dir), check
        self.knowledge = KnowledgeService(db, settings.storage_dir, settings.local_model_url, provider, settings.embedding_model,
                                           {"top_k": settings.knowledge_top_k, "similarity_threshold": settings.knowledge_similarity_threshold, "rerank": settings.knowledge_rerank})
        self.tasks = TaskEngine(db, provider, settings.default_model, self.files, self.knowledge)
        self.task_manager = BackgroundTaskManager(self.tasks, on_complete=self._task_complete)
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
                if path in ("", "/"):
                    return self.send_json(200, {"service": "Sovereign AI local backend", "ui": "Tkinter desktop", "status": "ready"})
                if path == "/api/health":
                    return self.send_json(200, server.health(server.db, server.provider, server.settings.storage_dir))
                username, _ = self.user()
                if not username:
                    return self.send_json(401, {"error": "Authentication required"})
                if path == "/api/conversations":
                    return self.send_json(200, [dict(row) for row in server.conversations.list()])
                if path == "/api/models":
                    models = list(server.provider.list_models())
                    # Keep the UI usable while Bionic is starting; health still reports
                    # whether the configured local model service is actually reachable.
                    return self.send_json(200, {"models": models or [server.settings.default_model]})
                if path == "/api/tasks":
                    return self.send_json(200, [dict(row) for row in server.db.execute("SELECT * FROM tasks ORDER BY id DESC")])
                if path.startswith("/api/tasks/"):
                    task_id = int(path.split("/")[-1])
                    row = server.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                    if not row: return self.send_json(404, {"error": "Task not found"})
                    steps = [dict(item) for item in server.db.execute("SELECT * FROM task_steps WHERE task_id=? ORDER BY step_number", (task_id,))]
                    result = {**dict(row), "steps": steps}
                    try:
                        workflow_state = json.loads(row["plan_json"] or "{}").get("workflow_state")
                        if workflow_state:
                            result["workflow_state"] = workflow_state
                            result["artifacts"] = workflow_state.get("artifacts", [])
                            result["verification_result"] = workflow_state.get("verification_result", {})
                    except (TypeError, json.JSONDecodeError):
                        # Older tasks may contain a non-JSON plan; their status remains usable.
                        pass
                    return self.send_json(200, result)
                if path == "/api/files":
                    return self.send_json(200, [dict(row) for row in server.files.list_files()])
                if path == "/api/knowledge/documents":
                    return self.send_json(200, [dict(row) for row in server.knowledge.list_documents()])
                if path == "/api/knowledge/search":
                    return self.send_json(400, {"error": "Use POST for knowledge search"})
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
                    if path == "/api/tasks":
                        task_id = server.task_manager.submit(payload["request"], username, payload.get("model"), payload.get("conversation_id"))
                        return self.send_json(202, {"task_id": task_id, "status": "queued"})
                    if path.startswith("/api/tasks/") and path.endswith("/approve"):
                        task_id = int(path.split("/")[3])
                        return self.send_json(200, server.tasks.approve(task_id, username))
                    if path.startswith("/api/tasks/") and path.endswith("/request-changes"):
                        task_id = int(path.split("/")[3])
                        return self.send_json(200, server.tasks.request_changes(task_id, payload.get("comment", ""), username))
                    if path.startswith("/api/tasks/") and path.endswith("/reject"):
                        task_id = int(path.split("/")[3])
                        return self.send_json(200, server.tasks.reject(task_id, payload.get("comment", ""), username))
                    if path == "/api/conversations":
                        conversation_id = server.conversations.create(payload.get("title", "New conversation"), payload.get("model", server.settings.default_model))
                        return self.send_json(201, {"id": conversation_id})
                    if path.startswith("/api/conversations/") and path.endswith("/chat"):
                        conversation_id = int(path.split("/")[3])
                        prompt = payload["content"].strip()
                        model = payload.get("model", server.settings.default_model)
                        task_id = server.task_manager.submit(prompt, username, model, conversation_id)
                        return self.send_json(202, {"task_id": task_id, "status": "queued"})
                    if path == "/api/files":
                        name = payload.get("name", "upload.txt")
                        raw = base64.b64decode(payload.get("content", ""), validate=True)
                        temp = server.settings.data_dir / (".upload_" + name.replace("\\", "_").replace("/", "_"))
                        temp.write_bytes(raw)
                        try:
                            stored = server.files.store(str(temp))
                            document = server.knowledge.ingest(str(temp), asynchronous=False, stored_name=stored["stored_name"])
                            return self.send_json(201, {"file": stored, "document": document})
                        finally:
                            temp.unlink(missing_ok=True)
                    if path == "/api/knowledge/search":
                        return self.send_json(200, server.knowledge.search(payload.get("question", ""), payload.get("filters"), payload.get("top_k")))
                    if path == "/api/knowledge/ask":
                        return self.send_json(200, server.knowledge.answer(payload["question"], server.provider, payload.get("model", server.settings.default_model), payload.get("filters")))
                    if path.startswith("/api/knowledge/documents/") and path.endswith("/reindex"):
                        server.knowledge.reindex(path.split("/")[4])
                        return self.send_json(202, {"queued": True})
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
                if path.startswith("/api/knowledge/documents/"):
                    server.knowledge.delete(path.split("/")[-1])
                    return self.send_json(200, {"deleted": True})
                return self.send_json(404, {"error": "Route not found"})

        self.httpd = ThreadingHTTPServer((host, port), Handler)

    def _task_complete(self, request, conversation_id, result):
        if conversation_id and result.get("status") == "awaiting_approval":
            self.conversations.add_message(conversation_id, "user", request)
            self.conversations.add_message(conversation_id, "assistant", result["result"])

    def serve_forever(self):
        self.logger.info("API server listening on %s", self.httpd.server_address)
        self.httpd.serve_forever()

    def shutdown(self):
        self.task_manager.shutdown()
        self.httpd.shutdown()
