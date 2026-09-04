import hashlib
import hmac
import secrets
import time
from typing import Optional
from .database import Database


class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self.sessions = {}

    def has_admin(self) -> bool:
        return self.db.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None

    def create_admin(self, username: str, password: str) -> None:
        self._validate(username, password)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        self.db.execute("INSERT INTO users(username,password_hash,password_salt) VALUES(?,?,?)",
                        (username.strip(), digest.hex(), salt.hex()))
        self.audit(username, "admin_created", "First-run administrator created")

    def login(self, username: str, password: str) -> bool:
        row = self.db.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
        if not row:
            return False
        salt = bytes.fromhex(row["password_salt"])
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000).hex()
        valid = hmac.compare_digest(digest, row["password_hash"])
        if valid:
            self.audit(username, "login", "Local login succeeded")
        return valid

    def create_session(self, username: str, password: str) -> str:
        if not self.login(username, password):
            raise ValueError("Invalid username or password")
        token = secrets.token_urlsafe(32)
        self.sessions[token] = (username.strip(), time.time() + 8 * 60 * 60)
        return token

    def session_user(self, token: str):
        session = self.sessions.get(token)
        if not session:
            return None
        username, expires = session
        if time.time() >= expires:
            self.sessions.pop(token, None)
            return None
        return username

    def logout(self, token: str) -> None:
        self.sessions.pop(token, None)

    def audit(self, username: Optional[str], action: str, details: str) -> None:
        self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)",
                        (username, action, details))

    @staticmethod
    def _validate(username: str, password: str) -> None:
        if len(username.strip()) < 3:
            raise ValueError("Username must contain at least 3 characters")
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters")
