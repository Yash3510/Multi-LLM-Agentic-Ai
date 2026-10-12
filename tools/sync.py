"""Start a working session from the latest trunk (master plan §6.5, AGENTS.md §1).

    uv run python tools/sync.py        (just sync)

Fetches 4ce-core from origin, fast-forwards the local 4ce-core, and lists the docs pages
that changed since your last sync. It never overwrites anything: local trunk commits that
aren't on origin stop it, and a trunk checked out in another worktree is left to that
worktree.
"""

import subprocess
import sys
from pathlib import Path

TRUNK = "4ce-core"
REMOTE = "origin"


class SyncError(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise SyncError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def _is_ancestor(repo: Path, old: str, new: str) -> bool:
    command = ["git", "-C", str(repo), "merge-base", "--is-ancestor", old, new]
    return subprocess.run(command, capture_output=True).returncode == 0


def _checked_out_elsewhere(repo: Path) -> bool:
    here = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    worktree = None
    for line in _git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            worktree = Path(line.removeprefix("worktree ")).resolve()
        elif line == f"branch refs/heads/{TRUNK}" and worktree != here:
            return True
    return False


def _fast_forward(repo: Path, upstream: str) -> str:
    local = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{TRUNK}"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if local and not _is_ancestor(repo, local, upstream):
        raise SyncError(
            f"your {TRUNK} has commits that aren't on {REMOTE}; push them through a PR or "
            "move them to a work branch, then sync again"
        )
    if _git(repo, "branch", "--show-current") == TRUNK:
        _git(repo, "merge", "--ff-only", "--quiet", upstream)
    elif _checked_out_elsewhere(repo):
        return f"{TRUNK} is checked out in another worktree; run just sync there"
    elif local:
        _git(repo, "update-ref", f"refs/heads/{TRUNK}", upstream, local)
    else:
        _git(repo, "branch", "--quiet", "--track", TRUNK, f"{REMOTE}/{TRUNK}")
    return f"{TRUNK} is at {upstream[:8]}"


def sync(repo: Path) -> list[str]:
    """Bring the trunk up to date; return the docs pages changed since the last sync."""
    _git(repo, "fetch", "--quiet", REMOTE, TRUNK)
    upstream = _git(repo, "rev-parse", f"{REMOTE}/{TRUNK}")
    print(_fast_forward(repo, upstream))
    stamp = repo / _git(repo, "rev-parse", "--git-path", "fource-last-sync")
    previous = stamp.read_text(encoding="utf-8").strip() if stamp.exists() else ""
    changed: list[str] = []
    if previous:
        diff = _git(repo, "diff", "--name-only", f"{previous}..{upstream}", "--", "docs/")
        changed = diff.split()
    stamp.write_text(upstream, encoding="utf-8")
    return changed


def main() -> int:
    repo = Path.cwd()
    try:
        changed = sync(repo)
    except SyncError as error:
        print(error)
        return 1
    if changed:
        print("Docs pages changed since your last sync:")
        print("\n".join(f"  {path}" for path in changed))
    else:
        print("No docs pages changed since your last sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
