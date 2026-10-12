"""Create new packages and docs pages from the templates, never by hand.

    uv run python tools/scaffold.py package <name>        core/<name>/ (just new-package)
    uv run python tools/scaffold.py doc <type> <name>     a docs page (just new-doc)

Doc types: architecture, adr, assurance, history, index, log, pack, research, runbook,
testing. For `log` the name is the branch; for `adr` a leading number ("0009-own-core")
picks a number reserved by the master plan, otherwise the next free one is used.
"""

import re
import sys
from datetime import date
from pathlib import Path

KEBAB = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")

DOC_FOLDERS = {
    "architecture": "docs/architecture",
    "assurance": "docs/assurance",
    "pack": "docs/packs",
    "research": "docs/research",
    "runbook": "docs/runbooks",
    "testing": "docs/testing",
}

PYPROJECT = """\
[project]
name = "fource-{name}"
version = "0.1.0"
description = "One line on what this package does."
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["uv_build>=0.13.0,<0.14"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "fource.{module}"
"""

README = """\
# fource-{name}

One paragraph on what this package is for and what it owns.

**Owner:** R1

## Public API

| Name | What it is |
| --- | --- |

## Tests

```
uv run pytest core/{name}
```
"""

INIT = '''\
"""One line on what this package does."""

__all__: list[str] = []
'''

FIRST_TEST = """\
import fource.{module}


def test_public_api_is_declared() -> None:
    assert isinstance(fource.{module}.__all__, list)
"""


def new_package(root: Path, name: str) -> Path:
    if not KEBAB.fullmatch(name):
        raise ValueError(f"'{name}' is not a kebab-case package name")
    package = root / "core" / name
    if package.exists():
        raise FileExistsError(package)
    module = name.replace("-", "_")
    files = {
        "pyproject.toml": PYPROJECT,
        "README.md": README,
        f"src/fource/{module}/__init__.py": INIT,
        f"src/fource/{module}/py.typed": "",
        f"tests/test_{module}.py": FIRST_TEST,
    }
    for relative, template in files.items():
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.format(name=name, module=module), encoding="utf-8")
    return package


def _title(name: str) -> str:
    words = re.sub(r"^\d+-", "", name).replace("-", " ").replace("_", " ")
    return words[:1].upper() + words[1:]


def _next_adr(root: Path) -> int:
    numbers = [int(p.name[:4]) for p in (root / "docs/adr").glob("[0-9][0-9][0-9][0-9]-*.md")]
    return max(numbers, default=0) + 1


def new_doc(root: Path, kind: str, name: str, today: date) -> Path:
    text = (root / "docs/templates" / f"{kind}.md").read_text(encoding="utf-8")
    title = _title(name)
    if kind == "log":
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        path = root / f"docs/log/{today:%Y/%m}/{today.isoformat()}-{slug}.md"
        text = text.replace("branch: <branch-name>", f"branch: {name}")
    elif kind == "adr":
        number = int(name[:4]) if re.match(r"\d{4}-", name) else _next_adr(root)
        slug = re.sub(r"^\d{4}-", "", name)
        path = root / f"docs/adr/{number:04d}-{slug}.md"
        text = text.replace("number: 0", f"number: {number}").replace("NNNN", f"{number:04d}")
    elif kind == "history":
        path = root / f"docs/history/{today.isoformat()}-{name}.md"
    elif kind == "index":
        path = root / "docs" / name / "README.md"
    else:
        path = root / DOC_FOLDERS[kind] / f"{name}.md"
    if path.exists():
        raise FileExistsError(path)
    # Templates quote placeholders to stay valid YAML; a filled-in date must be a real date.
    text = text.replace('"{{date}}"', today.isoformat()).replace("{{date}}", today.isoformat())
    text = text.replace("{{title}}", title)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if argv[:1] == ["package"] and len(argv) == 2:
        created = new_package(root, argv[1])
        print(f"created {created.relative_to(root)}; run `just setup` to install it")
    elif argv[:1] == ["doc"] and len(argv) == 3:
        created = new_doc(root, argv[1], argv[2], date.today())
        print(f"created {created.relative_to(root)}; link it from its folder's README.md")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
