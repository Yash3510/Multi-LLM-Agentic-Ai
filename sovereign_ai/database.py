import sqlite3
import threading
from pathlib import Path
from typing import Iterable


SCHEMA = [
    """CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL, password_salt TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        model TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT, original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL UNIQUE, content_type TEXT, size INTEGER NOT NULL,
        sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER,
        status TEXT NOT NULL DEFAULT 'queued', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )""",
    """CREATE TABLE IF NOT EXISTS task_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL, agent TEXT NOT NULL, action TEXT NOT NULL,
        model TEXT, status TEXT NOT NULL DEFAULT 'queued', input TEXT, output TEXT,
        verification TEXT, error TEXT, started_at TEXT, completed_at TEXT,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT NOT NULL,
        details TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY, original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
        file_type TEXT NOT NULL, size INTEGER NOT NULL, checksum TEXT NOT NULL,
        uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, modified_at TEXT,
        page_count INTEGER, processing_status TEXT NOT NULL DEFAULT 'uploaded',
        processing_error TEXT, version INTEGER NOT NULL DEFAULT 1,
        embedding_model TEXT, metadata_json TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY, document_id TEXT NOT NULL, document_version INTEGER NOT NULL,
        page INTEGER, section TEXT, block_number INTEGER, source_filename TEXT NOT NULL,
        content TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS knowledge_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued', stage TEXT NOT NULL DEFAULT 'uploaded',
        error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )""",
]


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.RLock()
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    def migrate(self) -> None:
        with self.connection:
            self.connection.execute(SCHEMA[0])
            applied = self.connection.execute("SELECT version FROM schema_migrations").fetchall()
            versions = {row[0] for row in applied}
            if 1 not in versions:
                for statement in SCHEMA[1:8]:
                    self.connection.execute(statement)
                self.connection.execute("INSERT INTO schema_migrations(version) VALUES (1)")
            if 2 not in versions:
                self.connection.execute(SCHEMA[6])
                columns = {row[1] for row in self.connection.execute("PRAGMA table_info(tasks)")}
                additions = {
                    "user_name": "TEXT", "plan_json": "TEXT", "current_step": "INTEGER DEFAULT 0",
                    "agent": "TEXT", "model": "TEXT", "input": "TEXT", "output": "TEXT",
                    "verification": "TEXT", "updated_at": "TEXT",
                }
                for name, definition in additions.items():
                    if name not in columns:
                        self.connection.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")
                self.connection.execute("INSERT INTO schema_migrations(version) VALUES (2)")
            if 3 not in versions:
                for statement in SCHEMA[8:11]:
                    self.connection.execute(statement)
                self.connection.execute("INSERT INTO schema_migrations(version) VALUES (3)")
            # Repair databases created by older Phase 2 builds that recorded the
            # migration but did not create every task table.
            self.connection.execute(SCHEMA[5])
            self.connection.execute(SCHEMA[6])
            columns = {row[1] for row in self.connection.execute("PRAGMA table_info(tasks)")}
            for name, definition in {
                "user_name": "TEXT", "plan_json": "TEXT", "current_step": "INTEGER DEFAULT 0",
                "agent": "TEXT", "model": "TEXT", "input": "TEXT", "output": "TEXT",
                "verification": "TEXT", "updated_at": "TEXT",
            }.items():
                if name not in columns:
                    self.connection.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")

    def execute(self, query: str, args: Iterable = ()) -> sqlite3.Cursor:
        with self._lock:
            with self.connection:
                return self.connection.execute(query, tuple(args))

    def close(self) -> None:
        self.connection.close()
