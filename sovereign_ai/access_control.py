import os
from pathlib import Path


class AccessControlService:
    """Persisted user grants for local file tools outside the default workspace."""

    def __init__(self, db, workspace):
        self.db = db
        self.workspace = Path(workspace).resolve()

    @staticmethod
    def protected(path):
        path = Path(path).resolve()
        if os.name != "nt":
            return False
        blocked = [
            Path(os.environ.get("WINDIR", r"C:\Windows")),
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path(os.environ.get("ProgramData", r"C:\ProgramData")),
        ]
        return any(path == root or root in path.parents for root in (item.resolve() for item in blocked))

    def _normalize(self, value):
        path = Path(value).expanduser().resolve()
        if self.protected(path):
            raise PermissionError("Windows and protected system paths cannot be granted")
        return path

    def grant(self, path, access="read", username="local-user"):
        if access not in {"read", "write"}:
            raise ValueError("Access must be read or write")
        target = self._normalize(path)
        if not target.exists():
            raise FileNotFoundError(str(target))
        self.db.execute(
            "INSERT INTO access_grants(path,access,created_by) VALUES(?,?,?) "
            "ON CONFLICT(path) DO UPDATE SET access=excluded.access,created_by=excluded.created_by",
            (str(target), access, username),
        )
        self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", (username, "access_granted", f"{access}:{target}"))
        return self.get(str(target))

    def revoke(self, path, username="local-user"):
        target = self._normalize(path)
        self.db.execute("DELETE FROM access_grants WHERE path=?", (str(target),))
        self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", (username, "access_revoked", str(target)))

    def get(self, path):
        target = self._normalize(path)
        row = self.db.execute("SELECT * FROM access_grants WHERE path=?", (str(target),)).fetchone()
        return dict(row) if row else None

    def list(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM access_grants ORDER BY path")]

    def allows(self, path, permission="read"):
        target = self._normalize(path)
        if target == self.workspace or self.workspace in target.parents:
            return True
        rows = self.db.execute("SELECT path,access FROM access_grants").fetchall()
        for row in rows:
            root = Path(row["path"])
            if target == root or root in target.parents:
                if permission == "read" or row["access"] == "write":
                    return True
        return False
