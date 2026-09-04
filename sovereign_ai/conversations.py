from .database import Database


class ConversationService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, title: str, model: str) -> int:
        row = self.db.execute("INSERT INTO conversations(title,model) VALUES(?,?)", (title, model))
        return row.lastrowid

    def list(self):
        return self.db.execute("SELECT * FROM conversations ORDER BY updated_at DESC, id DESC").fetchall()

    def messages(self, conversation_id: int):
        return self.db.execute("SELECT role,content FROM messages WHERE conversation_id=? ORDER BY id", (conversation_id,)).fetchall()

    def add_message(self, conversation_id: int, role: str, content: str):
        self.db.execute("INSERT INTO messages(conversation_id,role,content) VALUES(?,?,?)", (conversation_id, role, content))
        self.db.execute("UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (conversation_id,))
