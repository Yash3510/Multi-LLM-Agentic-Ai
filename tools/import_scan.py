"""No 4CE code imports a copyleft library it holds no commercial licence for (master plan §2.5).

    uv run python tools/import_scan.py build/sbom/python.cdx.json

Scans the imports of every Python file in core/, apps/ and packs/, maps each to the package
that provides it, and reads that package's licence from the SBOM. A commercially licensed
library may be imported only where its adapter lives (COMMERCIAL_PATHS).
"""

import ast
import json
import subprocess
import sys
from collections.abc import Mapping
from importlib.metadata import packages_distributions
from pathlib import Path

import licence_gate

SCANNED = ("core/", "apps/", "packs/")
# Where each commercially licensed library may be imported. The PDF adapter's path is set
# by its work package (WP-KN-01); until then PyMuPDF may be imported nowhere.
COMMERCIAL_PATHS: dict[str, tuple[str, ...]] = {"pymupdf": ()}


def imported_modules(source: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def check_imports(
    files: dict[str, str],
    dists: Mapping[str, list[str]],
    licences: dict[str, str],
    commercial_paths: dict[str, tuple[str, ...]],
) -> list[str]:
    problems: list[str] = []
    for path, source in sorted(files.items()):
        for name in sorted(imported_modules(source)):
            if name in sys.stdlib_module_names or name == "fource":
                continue
            if name not in dists:
                problems.append(f"{path}: imports {name}, which no installed package provides")
                continue
            for dist in dists[name]:
                key = licence_gate.normalise(dist)
                licence = licences.get(key, "")
                if key in commercial_paths:
                    allowed = commercial_paths[key]
                    if not (allowed and path.startswith(allowed)):
                        where = ", ".join(allowed) or "no module yet"
                        problems.append(
                            f"{path}: imports {name}; {dist} is allowed only in {where}"
                        )
                elif key not in licences:
                    problems.append(f"{path}: imports {name} from {dist}, which is not in the SBOM")
                elif licence_gate.denied(licence):
                    problems.append(
                        f"{path}: imports {name} from {dist} ({licence}), "
                        "a copyleft library 4CE has no commercial licence for"
                    )
    return problems


def _sbom_licences(sbom: Path) -> dict[str, str]:
    components = json.loads(sbom.read_text(encoding="utf-8")).get("components", [])
    reviewed = licence_gate.load_reviewed(licence_gate.REVIEWED_FILE.read_text(encoding="utf-8"))
    licences: dict[str, str] = {}
    for component in components:
        key = licence_gate.normalise(component["name"])
        texts = licence_gate.licence_texts(component)
        licences[key] = reviewed.get((key, component.get("version", "")), " AND ".join(texts))
    return licences


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", *SCANNED],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [p for p in listing.split("\0") if p.endswith(".py") and Path(p).exists()]
    files = {p: Path(p).read_text(encoding="utf-8") for p in paths}
    problems = check_imports(
        files, packages_distributions(), _sbom_licences(Path(argv[0])), COMMERCIAL_PATHS
    )
    print(f"{len(files)} files scanned")
    for line in problems:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
