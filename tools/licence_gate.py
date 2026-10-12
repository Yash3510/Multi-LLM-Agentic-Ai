"""Fail the build on any dependency whose licence the policy doesn't allow (master plan §2.5).

    uv run python tools/licence_gate.py build/sbom/python.cdx.json [more SBOMs]

The policy is master plan Appendix A; changing it is R4's decision, not a code change made
to get a build green. Every licence, and every option of an OR expression, must be allowed
anywhere. (Electing one option of an OR is what ADR-0036 proposes; until R4 accepts it, the
gate stays strict.) A package whose metadata doesn't name an SPDX licence is listed in
tools/licence-review.toml by a person who read its LICENSE file, for that exact version.
"""

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ALLOWED_ANYWHERE = {
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "ISC",
    "PostgreSQL",
    "PSF-2.0",
    "Zlib",
    "HPND",
    "Unicode-3.0",
    "Unicode-DFS-2016",
    "OFL-1.1",
    "CC0-1.0",
    "CC-BY-4.0",
}
REVIEW_REQUIRED = re.compile(r"MPL-2\.0|LGPL-.*|EPL-2\.0")
DENIED = re.compile(r"A?GPL-.*|SSPL-.*|BUSL-.*|RSAL.*|Elastic-.*|Commons-Clause|CC-BY-NC.*")

# Copyleft libraries 4CE holds a commercial licence for (Appendix A). The licence must be
# signed before the first install outside the team; the import scan limits where it is used.
COMMERCIAL = {"pymupdf"}

OWN_PACKAGE = re.compile(r"fource(-.*)?")
REVIEWED_FILE = Path(__file__).with_name("licence-review.toml")


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parts(expression: str) -> list[str]:
    return re.split(r"\s+(?:AND|OR)\s+", expression.replace("(", "").replace(")", "").strip())


def denied(expression: str) -> bool:
    return any(DENIED.fullmatch(part) for part in _parts(expression))


def problem(expression: str) -> str:
    """Why an SPDX expression isn't allowed anywhere, or "" if it is."""
    reasons: list[str] = []
    for part in _parts(expression):
        if part in ALLOWED_ANYWHERE:
            continue
        if REVIEW_REQUIRED.fullmatch(part):
            reasons.append(f"{part} needs a review and an ADR before use")
        elif DENIED.fullmatch(part):
            reasons.append(f"{part} is denied")
        else:
            reasons.append(f"'{part}' is not a licence the policy names")
    return "; ".join(reasons)


def licence_texts(component: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for entry in component.get("licenses", []):
        if "expression" in entry:
            texts.append(entry["expression"])
        else:
            licence = entry.get("license", {})
            texts.append(licence.get("id") or licence.get("name") or "")
    return texts


def check_components(
    components: list[dict[str, Any]], reviewed: dict[tuple[str, str], str]
) -> list[str]:
    problems: list[str] = []
    for component in components:
        name, version = component["name"], component.get("version", "")
        key = normalise(name)
        if OWN_PACKAGE.fullmatch(key) or key in COMMERCIAL:
            continue
        texts = (
            [reviewed[(key, version)]] if (key, version) in reviewed else licence_texts(component)
        )
        if not texts:
            problems.append(f"{name} {version}: no licence; read its LICENSE file and record it")
            continue
        reasons = [reason for text in texts if (reason := problem(text))]
        if reasons:
            problems.append(f"{name} {version}: {'; '.join(reasons)}")
    return problems


def load_reviewed(text: str) -> dict[tuple[str, str], str]:
    entries = tomllib.loads(text).get("package", [])
    return {(normalise(e["name"]), e["version"]): e["licence"] for e in entries}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    reviewed = load_reviewed(REVIEWED_FILE.read_text(encoding="utf-8"))
    problems: list[str] = []
    for sbom in argv:
        components = json.loads(Path(sbom).read_text(encoding="utf-8")).get("components", [])
        problems += check_components(components, reviewed)
        print(f"{sbom}: {len(components)} components checked")
    for line in problems:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
