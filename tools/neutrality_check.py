"""Keep sector vocabulary out of core/ and apps/ (master plan §6.1, §9).

    uv run python tools/neutrality_check.py

The terms live in tools/neutrality-terms.txt. A term matches as a whole word in any
identifier style (pump, Pumps, PumpCurve, max_pump, seal-leak), in file contents and in
paths. Industry words belong in a pack under packs/.
"""

import re
import subprocess
import sys
from pathlib import Path

SCANNED = ("core/", "apps/")
TERMS_FILE = Path(__file__).with_name("neutrality-terms.txt")
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def load_terms(text: str) -> list[str]:
    lines = (line.strip() for line in text.splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def _pattern(term: str) -> re.Pattern[str]:
    words = r"[\s_-]+".join(re.escape(word) for word in term.split())
    return re.compile(rf"(?<![a-z0-9]){words}(?:e?s)?(?![a-z0-9])", re.IGNORECASE)


def find_terms(path: str, text: str, terms: list[str]) -> list[str]:
    patterns = [(term, _pattern(term)) for term in terms]
    problems = [
        f"{path}: '{term}' in the path"
        for term, pattern in patterns
        if pattern.search(CAMEL_BOUNDARY.sub(" ", path))
    ]
    for number, line in enumerate(text.splitlines(), start=1):
        words = CAMEL_BOUNDARY.sub(" ", line)
        problems += [f"{path}:{number}: '{term}'" for term, p in patterns if p.search(words)]
    return problems


def main() -> int:
    terms = load_terms(TERMS_FILE.read_text(encoding="utf-8"))
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", *SCANNED],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    problems: list[str] = []
    for path in filter(None, listing.split("\0")):
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            text = ""  # binaries and deleted files: the path is still checked
        problems += find_terms(path, text, terms)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
