import hashlib
import json
import math
from urllib.request import Request, urlopen


class LocalEmbedder:
    """Local-only embedding client with a deterministic offline fallback."""

    def __init__(self, base_url, model="local-embedding", dimensions=256):
        self.base_url, self.model, self.dimensions = base_url.rstrip("/"), model, dimensions

    def embed(self, texts):
        try:
            body = json.dumps({"model": self.model, "input": texts}).encode()
            request = Request(self.base_url + "/embeddings", data=body, headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=60) as response:
                vectors = [item["embedding"] for item in json.load(response)["data"]]
            if vectors:
                self.dimensions = len(vectors[0])
            return vectors
        except Exception:
            return [self._fallback(text) for text in texts]

    def _fallback(self, text):
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
