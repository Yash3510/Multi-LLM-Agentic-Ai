from datetime import date
from pathlib import Path

import pytest

import docs_check
import repo_check
import scaffold

TODAY = date(2026, 10, 12)
TEMPLATES = Path(__file__).resolve().parents[2] / "docs" / "templates"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    templates = tmp_path / "docs" / "templates"
    templates.mkdir(parents=True)
    for template in TEMPLATES.glob("*.md"):
        (templates / template.name).write_text(template.read_text())
    (tmp_path / "docs" / "adr").mkdir()
    (tmp_path / "docs" / "adr" / "0035-frontend-foundations.md").write_text("x")
    return tmp_path


def files_under(root: Path, folder: str) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in (root / folder).rglob("*") if p.is_file())


def test_new_package_has_the_package_shape(repo: Path) -> None:
    scaffold.new_package(repo, "deep-cache")
    assert files_under(repo, "core/deep-cache") == [
        "core/deep-cache/README.md",
        "core/deep-cache/pyproject.toml",
        "core/deep-cache/src/fource/deep_cache/__init__.py",
        "core/deep-cache/src/fource/deep_cache/py.typed",
        "core/deep-cache/tests/test_deep_cache.py",
    ]
    pyproject = (repo / "core/deep-cache/pyproject.toml").read_text()
    assert 'name = "fource-deep-cache"' in pyproject
    assert 'module-name = "fource.deep_cache"' in pyproject
    assert repo_check.check_paths(files_under(repo, "core")) == []


def test_new_package_refuses_bad_or_taken_names(repo: Path) -> None:
    with pytest.raises(ValueError):
        scaffold.new_package(repo, "Deep_Cache")
    scaffold.new_package(repo, "rules")
    with pytest.raises(FileExistsError):
        scaffold.new_package(repo, "rules")


@pytest.mark.parametrize(
    ("kind", "name", "expected"),
    [
        ("architecture", "rule-engine", "docs/architecture/rule-engine.md"),
        ("runbook", "backup-and-restore", "docs/runbooks/backup-and-restore.md"),
        ("research", "turbovec-spike", "docs/research/turbovec-spike.md"),
        ("testing", "eval-methods", "docs/testing/eval-methods.md"),
        ("pack", "banking-lending", "docs/packs/banking-lending.md"),
        ("history", "owned-skeleton", "docs/history/2026-10-12-owned-skeleton.md"),
        (
            "log",
            "wp/RL-01-rule-engine-core",
            "docs/log/2026/10/2026-10-12-wp-rl-01-rule-engine-core.md",
        ),
        ("adr", "own-core", "docs/adr/0036-own-core.md"),
        ("adr", "0009-own-core", "docs/adr/0009-own-core.md"),
    ],
)
def test_new_doc_lands_where_the_rules_say(repo: Path, kind: str, name: str, expected: str) -> None:
    assert scaffold.new_doc(repo, kind, name, TODAY) == repo / expected


def test_new_doc_fills_in_the_placeholders(repo: Path) -> None:
    text = scaffold.new_doc(repo, "architecture", "rule-engine", TODAY).read_text()
    meta, body = docs_check.split(text)
    assert meta is not None
    assert meta["title"] == "Rule engine"
    assert meta["updated"] == TODAY
    assert body.startswith("\n# Rule engine\n")


def test_new_log_entry_records_its_branch(repo: Path) -> None:
    text = scaffold.new_doc(repo, "log", "wp/RL-01-rule-engine-core", TODAY).read_text()
    meta, _ = docs_check.split(text)
    assert meta is not None
    assert meta["branch"] == "wp/RL-01-rule-engine-core"
    assert meta["date"] == TODAY


def test_new_adr_is_numbered(repo: Path) -> None:
    text = scaffold.new_doc(repo, "adr", "own-core", TODAY).read_text()
    meta, body = docs_check.split(text)
    assert meta is not None and meta["number"] == 36
    assert "# ADR-0036: Own core" in body
