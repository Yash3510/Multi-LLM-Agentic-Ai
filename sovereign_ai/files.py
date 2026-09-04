import hashlib
import mimetypes
import shutil
from pathlib import Path
from .database import Database


ALLOWED = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".png", ".jpg", ".jpeg"}


class FileService:
    def __init__(self, db: Database, storage_dir: Path):
        self.db, self.storage_dir = db, storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def store(self, source: str) -> dict:
        path = Path(source)
        if path.suffix.lower() not in ALLOWED:
            raise ValueError("Supported files: PDF, DOCX, XLSX, PPTX, TXT, CSV, and images")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        stored = f"{digest}{path.suffix.lower()}"
        target = self.storage_dir / stored
        if not target.exists():
            shutil.copy2(path, target)
        row = self.db.execute("INSERT INTO files(original_name,stored_name,content_type,size,sha256) VALUES(?,?,?,?,?)",
                              (path.name, stored, mimetypes.guess_type(path.name)[0], path.stat().st_size, digest))
        return dict(self.db.execute("SELECT * FROM files WHERE id = ?", (row.lastrowid,)).fetchone())

    def list_files(self):
        return self.db.execute("SELECT * FROM files ORDER BY created_at DESC").fetchall()

    def delete(self, file_id: int) -> None:
        row = self.db.execute("SELECT stored_name FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row:
            raise FileNotFoundError("File not found")
        target = self.storage_dir / row["stored_name"]
        if target.exists():
            target.unlink()
        self.db.execute("DELETE FROM files WHERE id = ?", (file_id,))
