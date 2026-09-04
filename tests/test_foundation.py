import tempfile
import unittest
from pathlib import Path
from sovereign_ai.auth import AuthService
from sovereign_ai.database import Database
from sovereign_ai.files import FileService


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = Database(root / "test.db")

    def tearDown(self): self.db.close(); self.temp.cleanup()

    def test_admin_creation_and_login(self):
        auth = AuthService(self.db)
        self.assertFalse(auth.has_admin())
        auth.create_admin("admin", "strongpass")
        self.assertTrue(auth.has_admin())
        self.assertTrue(auth.login("admin", "strongpass"))
        self.assertFalse(auth.login("admin", "wrongpass"))

    def test_file_metadata_is_stored(self):
        root = Path(self.temp.name); source = root / "notes.txt"; source.write_text("local", encoding="utf-8")
        files = FileService(self.db, root / "files")
        row = files.store(str(source))
        self.assertEqual(row["original_name"], "notes.txt")
        self.assertTrue((root / "files" / row["stored_name"]).exists())


if __name__ == "__main__": unittest.main()
