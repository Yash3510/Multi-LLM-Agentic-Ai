import csv
import hashlib
import json
import logging
import mimetypes
import re
import threading
import uuid
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from .embeddings import LocalEmbedder
from .vector_store import TurbovecVectorStore


class DocumentParser:
    """Local parsers for common office/text formats; optional libraries extend PDF/OCR support."""

    def __init__(self, provider=None, vision_model="local-vision"):
        self.provider, self.vision_model = provider, vision_model

    def parse(self, path: Path):
        suffix = path.suffix.lower()
        if suffix in (".txt", ".csv"):
            return [{"page": 1, "section": "", "content": path.read_text(encoding="utf-8", errors="replace")}]
        if suffix in (".docx", ".xlsx", ".pptx"):
            return [{"page": 1, "section": "", "content": self._office_text(path)}]
        if suffix == ".pdf":
            return self._pdf(path)
        if suffix in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
            return self._image(path)
        raise ValueError("Unsupported document type")

    def _office_text(self, path):
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.endswith(".xml") and ("document" in name or "sheet" in name or "slide" in name)]
            values = []
            for name in names:
                root = ElementTree.fromstring(archive.read(name))
                texts = [value.text.strip() for value in root.iter() if value.text and value.text.strip()]
                if "document" in name:
                    values.append("Document paragraphs: " + " ".join(texts))
                elif "sheet" in name:
                    values.append(f"Worksheet {Path(name).stem}: " + " | ".join(texts))
                elif "slide" in name:
                    values.append(f"Slide {Path(name).stem}: " + " ".join(texts))
            return "\n".join(values)

    def _pdf(self, path):
        try:
            from pypdf import PdfReader
            pages = []
            for number, page in enumerate(PdfReader(str(path)).pages, 1):
                pages.append({"page": number, "section": "", "content": page.extract_text() or ""})
            if any(item["content"].strip() for item in pages):
                return pages
        except ImportError:
            pass
        ocr = self._ocr(path)
        if ocr:
            return ocr
        raise ValueError("PDF contains no extractable text and local OCR is unavailable")

    def _ocr(self, path):
        try:
            import pytesseract
            from pdf2image import convert_from_path
            if not shutil.which("tesseract") or not shutil.which("pdfinfo"):
                return []
            return [{"page": number, "section": "", "content": pytesseract.image_to_string(image)}
                    for number, image in enumerate(convert_from_path(str(path)), 1)]
        except Exception:
            return []

    @staticmethod
    def ocr_available():
        return bool(shutil.which("tesseract") and shutil.which("pdfinfo"))

    def _image(self, path):
        if not self.provider:
            return [{"page": 1, "section": "", "content": "", "visual": True}]
        try:
            description = self.provider.vision("Describe this document image for local knowledge retrieval.", path.read_bytes(), self.vision_model)
            return [{"page": 1, "section": "Image description", "content": description, "visual": True}]
        except (NotImplementedError, OSError):
            return [{"page": 1, "section": "", "content": "", "visual": True}]


class KnowledgeService:
    def __init__(self, db, storage_dir, local_model_url, provider=None, embedding_model="local-embedding", config=None):
        self.db, self.storage_dir = db, Path(storage_dir)
        self.embedder = LocalEmbedder(local_model_url, embedding_model, db=db)
        self.parser = DocumentParser(provider)
        self.index = TurbovecVectorStore(self.storage_dir.parent / "knowledge.tv")
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="knowledge")
        self.logger = logging.getLogger("sovereign_ai.knowledge")
        self.config = config or {}
        self.top_k = self.config.get("top_k", 5)
        self.threshold = self.config.get("similarity_threshold", -1.0)

    def ingest(self, source: str, asynchronous=True, stored_name=None):
        path = Path(source)
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        current = self.db.execute("SELECT * FROM documents WHERE original_name=? AND version=(SELECT MAX(version) FROM documents WHERE original_name=?)", (path.name, path.name)).fetchone()
        if current and current["checksum"] == checksum:
            return dict(current)
        version = (current["version"] + 1) if current else 1
        document_id = uuid.uuid5(uuid.NAMESPACE_URL, checksum + ":" + str(version)).hex
        stored_name = stored_name or path.name
        row = self.db.execute("INSERT INTO documents(id,original_name,stored_name,file_type,size,checksum,modified_at,version,metadata_json) VALUES(?,?,?,?,?,?,?,?,?)",
                              (document_id, path.name, stored_name, mimetypes.guess_type(path.name)[0] or path.suffix.lower(), path.stat().st_size, checksum, datetime.fromtimestamp(path.stat().st_mtime).isoformat(), version, "{}"))
        self.db.execute("INSERT INTO knowledge_jobs(document_id,status,stage) VALUES(?,?,?)", (document_id, "queued", "uploaded"))
        self._audit("document_uploaded", document_id, "queued")
        process_source = str(self.storage_dir / stored_name) if (self.storage_dir / stored_name).exists() else str(path)
        if asynchronous:
            self.executor.submit(self.process, document_id, process_source)
        else:
            self.process(document_id, process_source)
        return dict(self.db.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone())

    def process(self, document_id: str, source: str):
        try:
            self._stage(document_id, "parsing")
            pages = self.parser.parse(Path(source))
            self._stage(document_id, "chunking")
            document = self.db.execute("SELECT original_name,version FROM documents WHERE id=?", (document_id,)).fetchone()
            chunks = self._chunks(document_id, document["version"], document["original_name"], pages)
            self.db.execute("DELETE FROM document_chunks WHERE document_id=?", (document_id,))
            for chunk in chunks:
                self.db.execute("INSERT INTO document_chunks(id,document_id,document_version,page,section,block_number,source_filename,content,content_hash) VALUES(?,?,?,?,?,?,?,?,?)",
                                (chunk["chunk_id"], document_id, document["version"], chunk["page"], chunk["section"], chunk["block"], document["original_name"], chunk["content"], chunk["content_hash"]))
            self._stage(document_id, "embedding")
            vectors = self.embedder.embed([chunk["content"] for chunk in chunks]) if chunks else []
            self._stage(document_id, "indexing")
            self.index.delete([key for key, item in self.index.metadata.items() if item.get("document_id") == document_id])
            self.index.add(vectors, [{"vector_id": chunk["chunk_id"], "document_id": document_id, "metadata": {"page": chunk["page"], "section": chunk["section"], "version": document["version"]}} for chunk in chunks]) if chunks else None
            self.db.execute("UPDATE documents SET page_count=?,processing_status='ready',processing_error=NULL,embedding_model=? WHERE id=?", (len(pages), self.embedder.model, document_id))
            self._stage(document_id, "ready")
            self._audit("document_processed", document_id, "ready")
        except Exception as exc:
            self.db.execute("UPDATE documents SET processing_status='error',processing_error=? WHERE id=?", (str(exc), document_id))
            self._stage(document_id, "error", str(exc))
            self._audit("document_processing_failed", document_id, "error")

    def _chunks(self, document_id, version, filename, pages):
        chunks = []
        for page in pages:
            text = re.sub(r"\s+", " ", page.get("content", "")).strip()
            if not text:
                continue
            words, size = text.split(), 180
            for offset in range(0, len(words), size):
                content = " ".join(words[offset:offset + size])
                digest = hashlib.sha256(f"{document_id}:{version}:{page['page']}:{offset}:{content}".encode()).hexdigest()
                chunks.append({"chunk_id": digest[:32], "page": page["page"], "section": page.get("section", ""), "block": offset // size, "content": content, "content_hash": hashlib.sha256(content.encode()).hexdigest()})
        return chunks

    def search(self, question: str, filters=None, top_k=None):
        query = self.embedder.embed([question])[0]
        candidates = self.index.search(query, top_k or self.top_k, filters)
        results = []
        for candidate in candidates:
            if candidate["score"] < self.threshold:
                continue
            row = self.db.execute("SELECT * FROM document_chunks WHERE id=?", (candidate["vector_id"],)).fetchone()
            if row:
                results.append({**dict(row), "score": candidate["score"]})
        if not filters or filters.get("latest", True):
            results = [item for item in results if self._is_latest(item["document_id"], item["document_version"])]
        if self.config.get("rerank", True):
            question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
            for item in results:
                terms = set(re.findall(r"[a-z0-9]+", item["content"].lower()))
                item["rerank_score"] = item["score"] + 0.15 * len(question_terms & terms) / max(len(question_terms), 1)
            results.sort(key=lambda item: item["rerank_score"], reverse=True)
        self._audit("knowledge_search", None, f"results={len(results)}")
        return results

    def _is_latest(self, document_id, version):
        row = self.db.execute("SELECT original_name FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return False
        latest = self.db.execute("SELECT MAX(version) FROM documents WHERE original_name=?", (row["original_name"],)).fetchone()[0]
        return version == latest

    def answer(self, question: str, provider, model: str, filters=None):
        evidence = self.search(question, filters)
        if not evidence:
            return {"answer": "I could not find sufficient evidence in the local knowledge base to answer this reliably.", "citations": [], "evidence": []}
        context = "\n\n".join(f"[{index}] {item['source_filename']} page {item['page']} section {item['section']}:\n{item['content']}" for index, item in enumerate(evidence, 1))
        prompt = ("You are FRIDAY. Answer the question only from the supplied local evidence. "
                  "If it is insufficient, say so. Cite sources using [number] markers.\n\n"
                  "LOCAL EVIDENCE\n" + context + "\n\nQUESTION\n" + question)
        answer = provider.generate(prompt, model)
        citations = [{"source": item["source_filename"], "page": item["page"], "section": item["section"], "evidence": item["content"]} for item in evidence]
        return {"answer": answer, "citations": citations, "evidence": evidence}

    def delete(self, document_id):
        document = self.db.execute("SELECT stored_name FROM documents WHERE id=?", (document_id,)).fetchone()
        if not document:
            raise ValueError("Document not found")
        ids = [row[0] for row in self.db.execute("SELECT id FROM document_chunks WHERE document_id=?", (document_id,))]
        self.index.delete(ids)
        self.db.execute("DELETE FROM documents WHERE id=?", (document_id,))
        target = self.storage_dir / document["stored_name"]
        if target.exists():
            target.unlink()
        self.db.execute("DELETE FROM files WHERE stored_name=?", (document["stored_name"],))
        self._audit("document_deleted", document_id, "deleted")

    def reindex(self, document_id, asynchronous=True):
        row = self.db.execute("SELECT stored_name FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise ValueError("Document not found")
        source = self.storage_dir / row["stored_name"]
        if not source.exists():
            raise FileNotFoundError("Original local file is unavailable")
        self._stage(document_id, "queued")
        if asynchronous:
            self.executor.submit(self.process, document_id, str(source))
        else:
            self.process(document_id, str(source))
        self._audit("document_reindexed", document_id, "queued")

    def list_documents(self):
        return self.db.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()

    def _stage(self, document_id, stage, error=None):
        status = "error" if stage == "error" else ("ready" if stage == "ready" else "processing")
        self.db.execute("UPDATE knowledge_jobs SET status=?,stage=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE document_id=?", (status, stage, error, document_id))

    def _audit(self, action, document_id, status):
        self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", ("local-user", action, json.dumps({"document_id": document_id, "status": status})))
