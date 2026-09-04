import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentConfigurationTests(unittest.TestCase):
    def test_docker_declares_local_ocr_dependencies_and_healthcheck(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("tesseract-ocr", dockerfile)
        self.assertIn("poppler-utils", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("healthcheck:", compose)
        self.assertIn("sovereign_data", compose)

    def test_desktop_requirements_are_documented(self):
        running = (ROOT / "RUNNING.md").read_text(encoding="utf-8")
        self.assertIn("tkinter", running.lower())
        self.assertIn("docker compose up --build", running)
        self.assertIn("tesseract", running.lower())


if __name__ == "__main__": unittest.main()
