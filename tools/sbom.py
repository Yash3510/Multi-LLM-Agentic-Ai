"""Write the CycloneDX SBOM of the synced Python environment to build/sbom/ (master plan §2.5).

    uv run python tools/sbom.py

The SBOM is a generated artefact: CI attaches it to each release and it is never committed.
The generator runs through uvx at a pinned version, so every machine produces the same format.
"""

import subprocess
import sys
from pathlib import Path

GENERATOR = "cyclonedx-bom==7.5.0"
OUTPUT = Path("build/sbom/python.cdx.json")


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = ["uvx", "--from", GENERATOR, "cyclonedx-py", "environment", ".venv"]
    result = subprocess.run([*command, "--of", "JSON", "-o", str(OUTPUT)])
    if result.returncode == 0:
        print(f"wrote {OUTPUT}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
