import tempfile
import unittest
from pathlib import Path
from sovereign_ai.database import Database
from sovereign_ai.knowledge import KnowledgeService


class FakeProvider:
    def generate(self, prompt, model):
        self.last_prompt = prompt
        return "The procedure is described in the supplied evidence [1]."

    def vision(self, prompt, image, model):
        return "A local visual description."


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = Database(root / "knowledge.db")
        self.provider = FakeProvider()
        self.knowledge = KnowledgeService(self.db, root / "files", "http://127.0.0.1:9/v1", self.provider)

    def tearDown(self):
        self.knowledge.executor.shutdown(wait=True)
        self.db.close(); self.temp.cleanup()

    def test_ingest_retrieve_cite_and_answer_locally(self):
        source = Path(self.temp.name) / "maintenance.txt"
        source.write_text("Pump Maintenance: inspect the seal for leakage before operation.", encoding="utf-8")
        document = self.knowledge.ingest(str(source), asynchronous=False)
        self.assertEqual(document["processing_status"], "ready")
        results = self.knowledge.search("How should the pump be inspected?")
        self.assertEqual(results[0]["source_filename"], "maintenance.txt")
        answer = self.knowledge.answer("How should the pump be inspected?", self.provider, "local-model")
        self.assertEqual(answer["citations"][0]["page"], 1)
        self.assertIn("supplied evidence", answer["answer"])
        self.assertIn("maintenance.txt", self.provider.last_prompt)

    def test_duplicate_is_not_reprocessed_and_delete_removes_results(self):
        source = Path(self.temp.name) / "sop.txt"
        source.write_text("Use protective equipment.", encoding="utf-8")
        first = self.knowledge.ingest(str(source), asynchronous=False)
        duplicate = self.knowledge.ingest(str(source), asynchronous=False)
        self.assertEqual(first["id"], duplicate["id"])
        self.knowledge.delete(first["id"])
        self.assertEqual(self.knowledge.search("protective equipment"), [])

    def test_changed_upload_creates_new_version_and_old_version_is_not_retrieved(self):
        source = Path(self.temp.name) / "manual.txt"
        source.write_text("Version one says use gloves.", encoding="utf-8")
        first = self.knowledge.ingest(str(source), asynchronous=False)
        source.write_text("Version two says use a face shield.", encoding="utf-8")
        second = self.knowledge.ingest(str(source), asynchronous=False)
        self.assertEqual(second["version"], 2)
        results = self.knowledge.search("What protection is required?")
        self.assertTrue(all(row["document_version"] == 2 for row in results))

    def test_no_evidence_does_not_call_llm(self):
        answer = self.knowledge.answer("Unknown procedure", self.provider, "local-model")
        self.assertEqual(answer["citations"], [])
        self.assertIn("could not find sufficient evidence", answer["answer"])


if __name__ == "__main__": unittest.main()
