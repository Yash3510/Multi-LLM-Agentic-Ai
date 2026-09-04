import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BackendClient:
    """Small HTTP client used by the Tkinter workstation UI."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def request(self, method, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            try:
                detail = json.load(exc)
            except Exception:
                detail = {"error": str(exc)}
            raise RuntimeError(detail.get("error", str(exc))) from exc
        except (URLError, OSError) as exc:
            raise RuntimeError("Local backend unavailable: " + str(exc)) from exc

    def health(self):
        return self.request("GET", "/api/health")[1]

    def setup(self, username, password):
        return self.request("POST", "/api/setup", {"username": username, "password": password})[1]

    def login(self, username, password):
        result = self.request("POST", "/api/login", {"username": username, "password": password})[1]
        self.token = result["token"]
        return result

    def models(self):
        return self.request("GET", "/api/models")[1].get("models", [])

    def create_conversation(self, title, model):
        return self.request("POST", "/api/conversations", {"title": title, "model": model})[1]["id"]

    def submit_task(self, request, model, conversation_id=None):
        return self.request("POST", "/api/tasks", {"request": request, "model": model, "conversation_id": conversation_id})[1]

    def task(self, task_id):
        return self.request("GET", f"/api/tasks/{task_id}")[1]

    def approve(self, task_id):
        return self.request("POST", f"/api/tasks/{task_id}/approve", {})[1]

    def request_changes(self, task_id, comment):
        return self.request("POST", f"/api/tasks/{task_id}/request-changes", {"comment": comment})[1]

    def reject(self, task_id, comment):
        return self.request("POST", f"/api/tasks/{task_id}/reject", {"comment": comment})[1]

    def upload(self, path):
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return self.request("POST", "/api/files", {"name": path.name, "content": encoded})[1]

    def documents(self):
        return self.request("GET", "/api/knowledge/documents")[1]

    def search(self, question):
        return self.request("POST", "/api/knowledge/search", {"question": question})[1]

    def security_events(self):
        return self.request("GET", "/api/security/events")[1]
