import sqlite3
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
]


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
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
                self.connection.execute(SCHEMA[7])
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

    def execute(self, query: str, args: Iterable = ()) -> sqlite3.Cursor:
        with self.connection:
            return self.connection.execute(query, tuple(args))

    def close(self) -> None:
        self.connection.close()
