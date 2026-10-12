import subprocess
from pathlib import Path

import repo_check


def flagged(problems: list[str], path: str) -> bool:
    return any(problem.startswith(f"{path}:") for problem in problems)


GOOD_PACKAGE = [
    "core/rules/pyproject.toml",
    "core/rules/README.md",
    "core/rules/src/fource/rules/__init__.py",
    "core/rules/src/fource/rules/_internal/band_lookup.py",
    "core/rules/tests/test_engine.py",
]


def test_good_layout_passes() -> None:
    paths = [
        "README.md",
        "justfile",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/work-package.md",
        ".obsidian/app.json",
        "docs/architecture/rule-engine.md",
        "docs/log/2026/10/2026-10-12-wp-f-12-repo-check.md",
        "docs/history/2026-10-12-owned-skeleton.md",
        "deploy/third-party/minio/LICENSE",
        "packs/sector/industrial-energy/pack.yaml",
        "packs/sector/industrial-energy/rules/sop-mec-014.json",
        "core/rules/AGENTS.md",
        "docs/architecture/renewal.md",  # "new" inside a word is fine
        *GOOD_PACKAGE,
    ]
    assert repo_check.check_paths(paths) == []


def test_root_holds_only_the_listed_entries() -> None:
    problems = repo_check.check_paths(["README.md", "notes.txt", "scripts/run.sh"])
    assert flagged(problems, "notes.txt")
    assert flagged(problems, "scripts/run.sh")
    assert not flagged(problems, "README.md")


def test_github_and_obsidian_hold_only_shared_files() -> None:
    problems = repo_check.check_paths(
        [
            ".github/dependabot.yml",
            ".github/copilot-instructions.md",
            ".obsidian/core-plugins.json",
            ".obsidian/workspace.json",
        ]
    )
    assert flagged(problems, ".github/copilot-instructions.md")
    assert flagged(problems, ".obsidian/workspace.json")
    assert len(problems) == 2


def test_hidden_files_below_the_root_are_rejected() -> None:
    problems = repo_check.check_paths(
        ["core/rules/.cursorrules", "docs/.agent/rules.md", *GOOD_PACKAGE]
    )
    assert flagged(problems, "core/rules/.cursorrules")
    assert flagged(problems, "docs/.agent/rules.md")


def test_only_known_uppercase_names_are_allowed() -> None:
    problems = repo_check.check_paths(
        ["core/rules/GEMINI.md", "docs/Rule-Engine.md", "docs/README.md", *GOOD_PACKAGE]
    )
    assert flagged(problems, "core/rules/GEMINI.md")
    assert flagged(problems, "docs/Rule-Engine.md")
    assert not flagged(problems, "docs/README.md")


def test_naming_conventions() -> None:
    problems = repo_check.check_paths(
        [
            "packs/cross/Finance_Expenses/pack.yaml",
            "core/rules/src/fource/rules/RuleEngine.py",
            "deploy/config/grafana/Overview.json",
            *GOOD_PACKAGE,
        ]
    )
    assert flagged(problems, "packs/cross/Finance_Expenses/pack.yaml")
    assert flagged(problems, "core/rules/src/fource/rules/RuleEngine.py")
    assert flagged(problems, "deploy/config/grafana/Overview.json")
    assert len(problems) == 3


def test_banned_words_and_spaces() -> None:
    problems = repo_check.check_paths(
        [
            "docs/architecture/rules-final.md",
            "packs/sector/old/pack.yaml",
            "docs/my page.md",
            "deploy/compose/core-v2.yml",
            "docs/research/test2.md",
        ]
    )
    for path in (
        "docs/architecture/rules-final.md",
        "packs/sector/old/pack.yaml",
        "docs/my page.md",
        "deploy/compose/core-v2.yml",
        "docs/research/test2.md",
    ):
        assert flagged(problems, path)


def test_dates_only_in_dated_folders() -> None:
    problems = repo_check.check_paths(
        ["docs/research/2026-10-12-notes.md", "docs/assurance/2026-10-12/core.md"]
    )
    assert flagged(problems, "docs/research/2026-10-12-notes.md")
    assert not flagged(problems, "docs/assurance/2026-10-12/core.md")


def test_every_package_has_a_readme_and_tests() -> None:
    problems = repo_check.check_paths(
        [*GOOD_PACKAGE, "core/calc/pyproject.toml", "core/calc/src/fource/calc/__init__.py"]
    )
    assert any("core/calc" in p and "README.md" in p for p in problems)
    assert any("core/calc" in p and "tests" in p for p in problems)
    assert not any(p.startswith("core/rules") for p in problems)


def test_only_uv_dependency_files() -> None:
    problems = repo_check.check_paths(
        [*GOOD_PACKAGE, "core/rules/requirements-dev.txt", "core/rules/Pipfile"]
    )
    assert flagged(problems, "core/rules/requirements-dev.txt")
    assert flagged(problems, "core/rules/Pipfile")


def test_contents_never_tell_anyone_to_use_pip() -> None:
    install = "pip" + " install"  # split so this file doesn't trip the check it tests
    problems = repo_check.check_contents(
        {"deploy/compose/core.yml": f"command: {install} fource", "README.md": "uv sync"}
    )
    assert flagged(problems, "deploy/compose/core.yml")
    assert not flagged(problems, "README.md")


def test_todos_carry_an_issue_number() -> None:
    marker = "TO" + "DO"
    problems = repo_check.check_contents(
        {
            "core/rules/src/fource/rules/engine.py": f"# {marker}: handle units\n",
            "core/calc/src/fource/calc/engine.py": f"# {marker}(#12): handle units\n",
        }
    )
    assert flagged(problems, "core/rules/src/fource/rules/engine.py")
    assert not flagged(problems, "core/calc/src/fource/calc/engine.py")


def test_files_over_one_megabyte_must_be_in_lfs() -> None:
    problems = repo_check.check_sizes(
        {"packs/sector/x/demo/report.pdf": 2_000_000, "docs/README.md": 4_000}
    )
    assert flagged(problems, "packs/sector/x/demo/report.pdf")
    assert len(problems) == 1


MANIFEST = """\
id: example-sector
title: Example Sector
version: 0.1.0
kind: sector
risk_tier: 3
summary: An example.
locales: [en-IN]
"""


def test_every_pack_manifest_validates() -> None:
    good = {"packs/sector/example-sector/pack.yaml": MANIFEST}
    assert repo_check.check_packs(good) == []
    bad = {
        "packs/sector/example-sector/pack.yaml": MANIFEST.replace("risk_tier: 3", "risk_tier: 9")
    }
    problems = repo_check.check_packs(bad)
    assert problems and problems[0].startswith("packs/sector/example-sector/pack.yaml:")


def test_a_pack_lives_under_its_own_id_and_kind() -> None:
    misplaced = {"packs/cross/other-name/pack.yaml": MANIFEST}
    problems = repo_check.check_packs(misplaced)
    assert any("other-name" in p for p in problems)
    assert any("cross" in p for p in problems)


def test_a_pack_folder_needs_a_manifest() -> None:
    problems = repo_check.check_paths(["packs/sector/example-sector/README.md"])
    assert problems == ["packs/sector/example-sector: pack has no pack.yaml"]


def test_commit_subjects_are_conventional() -> None:
    assert repo_check.check_subject("feat(rules): add authority rule type") == []
    assert repo_check.check_subject("docs: add AGENTS.md") == []
    assert repo_check.check_subject("fix(industrial-energy): correct seal leak band") == []
    assert repo_check.check_subject("Added stuff") != []
    assert repo_check.check_subject("feat(rules):missing space") != []
    assert repo_check.check_subject("feature(rules): unknown type") != []


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def test_empty_and_whitespace_only_commits_are_rejected(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "dev@example.com")
    git(tmp_path, "config", "user.name", "Dev")
    (tmp_path / "a.txt").write_text("one\n")
    git(tmp_path, "add", "a.txt")
    git(tmp_path, "commit", "-q", "-m", "chore: start")
    base = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "chore: nothing")
    (tmp_path / "a.txt").write_text("one   \n")
    git(tmp_path, "commit", "-q", "-am", "chore: spaces")
    (tmp_path / "a.txt").write_text("two\n")
    git(tmp_path, "commit", "-q", "-am", "feat: real change")

    problems = repo_check.check_commits(f"{base}..HEAD", tmp_path)
    assert any("chore: nothing" in p and "empty" in p for p in problems)
    assert any("chore: spaces" in p and "whitespace" in p for p in problems)
    assert not any("feat: real change" in p for p in problems)
