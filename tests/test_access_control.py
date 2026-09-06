import os
import tempfile
import unittest
from pathlib import Path

from sovereign_ai.access_control import AccessControlService
from sovereign_ai.database import Database
from sovereign_ai.tools import ToolRegistry


class AccessControlTests(unittest.TestCase):
    def test_grant_and_revoke_control_external_file_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "access.db")
            workspace = root / "workspace"
            external = root / "external.txt"
            external.write_text("private local evidence", encoding="utf-8")
            registry = ToolRegistry(db=db, workspace=workspace)
            denied = registry.execute_tool("read_file", {"path": str(external)})
            self.assertFalse(denied["success"])
            access = AccessControlService(db, workspace)
            access.grant(external, "read")
            allowed = registry.execute_tool("read_file", {"path": str(external)})
            self.assertTrue(allowed["success"])
            write_denied = registry.execute_tool("write_file", {"path": str(external), "content": "changed"}, permission="write")
            self.assertFalse(write_denied["success"])
            access.revoke(external)
            revoked = registry.execute_tool("read_file", {"path": str(external)})
            self.assertFalse(revoked["success"])
            db.close()

    @unittest.skipUnless(os.name == "nt", "Windows protected path check")
    def test_windows_system_path_cannot_be_granted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = Database(root / "access.db")
            access = AccessControlService(db, root / "workspace")
            with self.assertRaises(PermissionError): access.grant(Path(os.environ.get("WINDIR", r"C:\Windows")), "read")
            db.close()


if __name__ == "__main__": unittest.main()
