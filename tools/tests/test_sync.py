import subprocess
from pathlib import Path

import pytest

import sync


def git(repo: Path, *args: str) -> str:
    command = ["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, path: str, text: str, message: str) -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text, encoding="utf-8")
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", message)


@pytest.fixture
def team(tmp_path: Path) -> tuple[Path, Path]:
    """A shared remote, a teammate's clone that pushes, and the developer's clone."""
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    teammate = tmp_path / "teammate"
    git(tmp_path, "init", "-q", "-b", sync.TRUNK, str(teammate))
    git(teammate, "config", "user.email", "t@example.com")
    git(teammate, "config", "user.name", "T")
    git(teammate, "remote", "add", "origin", str(remote))
    commit(teammate, "docs/README.md", "index\n", "docs: start")
    git(teammate, "push", "-q", "origin", sync.TRUNK)
    developer = tmp_path / "developer"
    git(tmp_path, "clone", "-q", "--branch", sync.TRUNK, str(remote), str(developer))
    git(developer, "config", "user.email", "d@example.com")
    git(developer, "config", "user.name", "D")
    return teammate, developer


def test_first_sync_records_where_it_started(team: tuple[Path, Path]) -> None:
    _, developer = team
    assert sync.sync(developer) == []


def test_sync_fast_forwards_and_lists_docs_changed_since_last_time(
    team: tuple[Path, Path],
) -> None:
    teammate, developer = team
    sync.sync(developer)
    commit(teammate, "docs/state.md", "now\n", "docs: state")
    commit(teammate, "core/x.py", "x = 1\n", "feat: x")
    git(teammate, "push", "-q", "origin", sync.TRUNK)

    assert sync.sync(developer) == ["docs/state.md"]
    assert git(developer, "rev-parse", "HEAD") == git(teammate, "rev-parse", "HEAD")
    assert sync.sync(developer) == []


def test_sync_updates_the_trunk_while_on_a_work_branch(team: tuple[Path, Path]) -> None:
    teammate, developer = team
    git(developer, "switch", "-q", "-c", "wp/F-99-example")
    commit(teammate, "docs/a.md", "a\n", "docs: a")
    git(teammate, "push", "-q", "origin", sync.TRUNK)

    sync.sync(developer)
    assert git(developer, "rev-parse", sync.TRUNK) == git(teammate, "rev-parse", "HEAD")
    assert git(developer, "branch", "--show-current") == "wp/F-99-example"


def test_sync_never_overwrites_local_trunk_commits(team: tuple[Path, Path]) -> None:
    teammate, developer = team
    commit(developer, "docs/mine.md", "mine\n", "docs: mine")
    commit(teammate, "docs/theirs.md", "theirs\n", "docs: theirs")
    git(teammate, "push", "-q", "origin", sync.TRUNK)

    with pytest.raises(sync.SyncError):
        sync.sync(developer)
    assert (developer / "docs/mine.md").exists()


def test_sync_never_overwrites_the_trunk_from_a_work_branch(team: tuple[Path, Path]) -> None:
    teammate, developer = team
    commit(developer, "docs/mine.md", "mine\n", "docs: mine")
    mine = git(developer, "rev-parse", "HEAD")
    git(developer, "switch", "-q", "-c", "wp/F-99-example")
    commit(teammate, "docs/theirs.md", "theirs\n", "docs: theirs")
    git(teammate, "push", "-q", "origin", sync.TRUNK)

    with pytest.raises(sync.SyncError):
        sync.sync(developer)
    assert git(developer, "rev-parse", sync.TRUNK) == mine
