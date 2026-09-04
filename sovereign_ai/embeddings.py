import hashlib
import json
import math
from urllib.request import Request, urlopen
from .config import is_local_endpoint
from .security import record_blocked


class LocalEmbedder:
    """Local-only embedding client with a deterministic offline fallback."""

    def __init__(self, base_url, model="local-embedding", dimensions=256, sovereign_mode=True, db=None):
        if sovereign_mode and not is_local_endpoint(base_url):
            if db: record_blocked(db, base_url, "non-local embedding endpoint rejected")
            raise ValueError("Sovereign mode only permits local embedding endpoints")
        self.base_url, self.model, self.dimensions = base_url.rstrip("/"), model, dimensions
        self.db = db

    def embed(self, texts):
        try:
            body = json.dumps({"model": self.model, "input": texts}).encode()
            request = Request(self.base_url + "/embeddings", data=body, headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=60) as response:
                vectors = [item["embedding"] for item in json.load(response)["data"]]
            if vectors:
                self.dimensions = len(vectors[0])
            if self.db: self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", ("system", "embedding_invocation", json.dumps({"model": self.model, "local": True, "success": True})))
            return vectors
        except Exception:
            if self.db: self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", ("system", "embedding_fallback", json.dumps({"model": self.model, "local": True, "success": True})))
            return [self._fallback(text) for text in texts]

    def _fallback(self, text):
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
