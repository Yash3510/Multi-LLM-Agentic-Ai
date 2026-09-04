import json
import math
from pathlib import Path


class VectorStore:
    def add(self, vectors, metadata): raise NotImplementedError
    def search(self, query_vector, top_k, filters=None): raise NotImplementedError
    def delete(self, ids): raise NotImplementedError
    def save(self): raise NotImplementedError


class TurbovecVectorStore(VectorStore):
    """Turbovec adapter with a transparent JSON cosine fallback for local setup."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata = {}
        self.vectors = {}
        self.index = None
        self._load_fallback()

    def _load_fallback(self):
        if self.path.with_suffix(".json").exists():
            payload = json.loads(self.path.with_suffix(".json").read_text(encoding="utf-8"))
            self.metadata, self.vectors = payload.get("metadata", {}), payload.get("vectors", {})

    def add(self, vectors, metadata):
        for vector, item in zip(vectors, metadata):
            vector_id = str(item["vector_id"])
            self.vectors[vector_id] = vector
            self.metadata[vector_id] = item
        self._rebuild_turbovec()
        self.save()

    def _rebuild_turbovec(self):
        try:
            import numpy as np
            from turbovec import IdMapIndex
            dimension = len(next(iter(self.vectors.values())))
            index = IdMapIndex(dim=dimension, bit_width=4)
            ids = np.asarray([int(key[:16], 16) for key in self.vectors], dtype=np.uint64)
            index.add_with_ids(np.asarray(list(self.vectors.values()), dtype=np.float32), ids)
            self.index, self._numeric_ids = index, dict(zip(ids.tolist(), self.vectors.keys()))
        except (ImportError, ModuleNotFoundError, ValueError, TypeError):
            self.index = None

    def search(self, query_vector, top_k, filters=None):
        allowed = [key for key, item in self.metadata.items() if not filters or all(item.get("metadata", {}).get(k) == v for k, v in filters.items())]
        if not allowed:
            return []
        if self.index is not None:
            import numpy as np
            numeric = np.asarray([int(key[:16], 16) for key in allowed], dtype=np.uint64)
            scores, ids = self.index.search(np.asarray([query_vector], dtype=np.float32), k=min(top_k, len(allowed)), allowlist=numeric)
            return [{**self.metadata[self._numeric_ids[int(vector_id)]], "score": float(score)} for score, vector_id in zip(scores[0], ids[0])]
        def cosine(vector):
            dot = sum(a * b for a, b in zip(query_vector, vector))
            norm_a = math.sqrt(sum(a * a for a in query_vector)) or 1.0
            norm_b = math.sqrt(sum(b * b for b in vector)) or 1.0
            return dot / (norm_a * norm_b)
        ranked = sorted(((cosine(self.vectors[key]), key) for key in allowed), reverse=True)
        return [{**self.metadata[key], "score": score} for score, key in ranked[:top_k]]

    def delete(self, ids):
        for vector_id in ids:
            self.vectors.pop(str(vector_id), None)
            self.metadata.pop(str(vector_id), None)
        self._rebuild_turbovec()
        self.save()

    def save(self):
        self.path.with_suffix(".json").write_text(json.dumps({"metadata": self.metadata, "vectors": self.vectors}), encoding="utf-8")
        if self.index is not None:
            self.index.write(str(self.path))
