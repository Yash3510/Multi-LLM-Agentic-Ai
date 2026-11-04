"""Create .env from .env.example with fresh secrets, once (run by just setup).

    uv run python tools/dev/env.py

Every value that is exactly `change-me` gets its own random secret. Comments, other values
and ${VAR} references are kept. An existing .env is never touched.
"""

import re
import secrets
import sys
from collections.abc import Callable
from pathlib import Path

PLACEHOLDER = re.compile(r"^(?P<name>[A-Z][A-Z0-9_]*)=change-me$", re.MULTILINE)
SecretMaker = Callable[[], str]


def random_secret() -> str:
    return secrets.token_urlsafe(32)


def fill(example: str, make_secret: SecretMaker) -> str:
    return PLACEHOLDER.sub(lambda match: f"{match['name']}={make_secret()}", example)


def ensure_env(root: Path) -> bool:
    target = root / ".env"
    if target.exists():
        return False
    example = (root / ".env.example").read_text(encoding="utf-8")
    target.write_text(fill(example, random_secret), encoding="utf-8", newline="\n")
    return True


def main() -> int:
    created = ensure_env(Path.cwd())
    print("created .env with fresh secrets" if created else "kept the existing .env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
