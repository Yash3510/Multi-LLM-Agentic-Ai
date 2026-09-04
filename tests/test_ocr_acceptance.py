import shutil
import tempfile
import unittest
from pathlib import Path
from sovereign_ai.knowledge import DocumentParser


class OcrAcceptanceTests(unittest.TestCase):
    def test_native_ocr_tools_are_available(self):
        if not DocumentParser.ocr_available():
            self.skipTest("tesseract and pdfinfo are not installed in this runtime; Docker installs both")
        self.assertIsNotNone(shutil.which("tesseract"))
        self.assertIsNotNone(shutil.which("pdfinfo"))

    def test_scanned_pdf_fixture_uses_local_ocr_when_available(self):
        if not DocumentParser.ocr_available():
            self.skipTest("native OCR tools unavailable")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow unavailable")
        temp = tempfile.TemporaryDirectory()
        image = Image.new("RGB", (1400, 300), "white")
        ImageDraw.Draw(image).text((30, 100), "DEMO TEST: Compressor C-101 requires inspection before startup.", fill="black")
        pdf = Path(temp.name) / "scanned_demo.pdf"
        image.save(pdf, "PDF", resolution=150.0)
        pages = DocumentParser().parse(pdf)
        self.assertTrue(any("C-101" in page["content"] for page in pages))
        self.assertEqual(pages[0]["page"], 1)
        temp.cleanup()


if __name__ == "__main__": unittest.main()
