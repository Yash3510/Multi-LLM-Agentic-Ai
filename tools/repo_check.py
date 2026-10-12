"""Keep the repository's shape as master plan §6.4 and §6.5 define it.

    uv run python tools/repo_check.py                    every file git tracks or would add
    uv run python tools/repo_check.py --commits A..B     the commits in a range
    uv run python tools/repo_check.py --commit-msg FILE  a commit message (git hook)

Each problem is printed as "<path or commit>: <what is wrong>". Exit code 1 if any.
"""

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT_ENTRIES = {
    ".github",
    ".obsidian",
    "apps",
    "core",
    "packs",
    "skills",
    "tests",
    "evals",
    "deploy",
    "docs",
    "tools",
    ".editorconfig",
    ".env.example",
    ".gitattributes",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".python-version",
    "justfile",
    "pyproject.toml",
    "uv.lock",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
}

# GitHub and Obsidian dictate these names; anything else there is a tool's private file.
GITHUB_ENTRIES = {
    "CODEOWNERS",
    "pull_request_template.md",
    "ISSUE_TEMPLATE",
    "dependabot.yml",
    "workflows",
}
OBSIDIAN_ENTRIES = {"app.json", "core-plugins.json", "templates.json"}

# Upper-case names allowed below the root. Everything else is lower case, so a tool's own
# instruction file (FOO.md, .foorules, .foo/) never slips in unnoticed.
UPPERCASE_NAMES = {
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "LICENSE",
    "NOTICE",
    "VERSION",
    "SOURCE",
}

KEBAB = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SNAKE = re.compile(r"_?[a-z][a-z0-9_]*")
PYTHON_FILE = re.compile(r"_{0,2}[a-z][a-z0-9_]*\.py")
OTHER_FILE = re.compile(r"[a-z0-9][a-z0-9.-]*")

BANNED_WORDS = {"final", "new", "old", "backup", "copy", "temp", "tmp"}
BANNED_TOKEN = re.compile(r"v\d+|test\d+|copy\d+")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
DATED_FOLDERS = ("docs/log/", "docs/history/", "docs/assurance/")

NON_UV_FILES = re.compile(r"requirements.*\.txt|setup\.py|Pipfile|Pipfile\.lock|poetry\.lock")
PIP_INSTALL = re.compile(r"\bpip3?\s+install\b")
TODO_WITHOUT_ISSUE = re.compile(r"(#|//)\s*TODO(?!\(#\d+\))")
CODE_SUFFIXES = {".py", ".ts", ".js", ".svelte", ".sh", ".yml", ".yaml", ".toml"}

MAX_BYTES = 1_000_000

COMMIT_SUBJECT = re.compile(
    r"(feat|fix|docs|test|refactor|perf|build|ci|chore|revert)(\([a-z0-9][a-z0-9-]*\))?!?: \S.*"
)


def check_paths(paths: list[str]) -> list[str]:
    """Layout, naming and package rules for a list of repository paths."""
    problems = [f"{path}: {reason}" for path in paths if (reason := _path_problem(path))]
    return problems + _package_problems(paths)


def _path_problem(path: str) -> str:
    parts = PurePosixPath(path).parts
    top = parts[0]
    if top not in ROOT_ENTRIES:
        return f"'{top}' is not allowed at the root (see §6.4)"
    if top == ".github" and len(parts) > 1:
        return "" if parts[1] in GITHUB_ENTRIES else "not a shared GitHub file"
    if top == ".obsidian" and len(parts) > 1:
        return "" if parts[1] in OBSIDIAN_ENTRIES else "not a shared Obsidian setting"
    if len(parts) == 1:
        return ""

    reasons: list[str] = []
    in_src = False
    for depth, name in enumerate(parts[1:], start=1):
        is_file = depth == len(parts) - 1
        if " " in name:
            reasons.append("spaces in a name")
        if name.startswith("."):
            reasons.append(f"hidden file or folder '{name}' (tool files stay local)")
        elif is_file:
            reasons += _file_name_problems(name)
        elif not (KEBAB.fullmatch(name) or (in_src and SNAKE.fullmatch(name))):
            reasons.append(f"folder '{name}' is not kebab-case")
        tokens = re.split(r"[-_.]", name.lower())
        if BANNED_WORDS.intersection(tokens) or any(BANNED_TOKEN.fullmatch(t) for t in tokens):
            reasons.append(f"'{name}' contains a version or status word")
        if DATE.search(name) and not path.startswith(DATED_FOLDERS):
            reasons.append(f"'{name}' contains a date")
        if NON_UV_FILES.fullmatch(name):
            reasons.append("dependencies are declared in pyproject.toml and locked by uv only")
        in_src = in_src or name == "src"
    return "; ".join(dict.fromkeys(reasons))


def _file_name_problems(name: str) -> list[str]:
    if name in UPPERCASE_NAMES:
        return []
    if name.endswith(".py"):
        return [] if PYTHON_FILE.fullmatch(name) else [f"'{name}' is not a snake_case module"]
    return [] if OTHER_FILE.fullmatch(name) else [f"'{name}' is not a lower-case kebab name"]


def _package_problems(paths: list[str]) -> list[str]:
    packages: dict[str, set[str]] = {}
    for path in paths:
        parts = PurePosixPath(path).parts
        if parts[0] in ("core", "apps") and len(parts) > 2:
            packages.setdefault(f"{parts[0]}/{parts[1]}", set()).add("/".join(parts[2:]))
    problems: list[str] = []
    for package, files in sorted(packages.items()):
        if "README.md" not in files:
            problems.append(f"{package}: package has no README.md")
        if not any(f.startswith("tests/") for f in files):
            problems.append(f"{package}: package has no tests")
    return problems


def check_contents(files: dict[str, str]) -> list[str]:
    """Text rules: nobody is told to use pip, and every TODO in code names its issue."""
    problems: list[str] = []
    for path, text in files.items():
        if PIP_INSTALL.search(text):
            problems.append(f"{path}: uses pip; use uv (see §6.5)")
        if PurePosixPath(path).suffix in CODE_SUFFIXES and TODO_WITHOUT_ISSUE.search(text):
            problems.append(f"{path}: a TODO without an issue number, e.g. TODO(#123)")
    return problems


def check_sizes(sizes: dict[str, int]) -> list[str]:
    """Blobs over 1 MB belong in Git LFS (an LFS pointer is only a few hundred bytes)."""
    return [
        f"{path}: {size:,} bytes; files over 1 MB go through Git LFS"
        for path, size in sizes.items()
        if size > MAX_BYTES
    ]


def check_subject(subject: str) -> list[str]:
    if COMMIT_SUBJECT.fullmatch(subject):
        return []
    return [f"'{subject}' is not a Conventional Commit, e.g. 'feat(rules): add authority rule'"]


def check_commits(rev_range: str, repo: Path) -> list[str]:
    problems: list[str] = []
    for commit in _git(repo, "rev-list", "--reverse", "--no-merges", rev_range).split():
        subject = _git(repo, "log", "-1", "--format=%s", commit)
        label = f"{commit[:8]} {subject}"
        problems += [f"{label}: {p}" for p in check_subject(subject)]
        parent = f"{commit}^" if _has_parent(repo, commit) else EMPTY_TREE
        if not _differs(repo, parent, commit):
            problems.append(f"{label}: empty commit")
        elif not _differs(repo, parent, commit, "-w", "--ignore-blank-lines"):
            problems.append(f"{label}: whitespace-only commit")
    return problems


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's well-known empty tree


def _has_parent(repo: Path, commit: str) -> bool:
    return len(_git(repo, "rev-list", "--parents", "-n", "1", commit).split()) > 1


def _differs(repo: Path, old: str, new: str, *options: str) -> bool:
    result = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", *options, old, new])
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return result.returncode == 1


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _files(repo: Path) -> dict[str, int]:
    """Every file git tracks or would add, with its size: the stored blob for tracked files
    (an LFS pointer is tiny), the file on disk for ones not added yet."""
    listing = _git(repo, "ls-files", "-z", "--format=%(objectsize) %(path)")
    sizes: dict[str, int] = {}
    for entry in filter(None, listing.split("\0")):
        size, path = entry.split(" ", 1)
        sizes[path] = int(size)
    untracked = _git(repo, "ls-files", "-z", "--others", "--exclude-standard")
    for path in filter(None, untracked.split("\0")):
        sizes[path] = (repo / path).stat().st_size
    return sizes


def _texts(repo: Path, paths: list[str]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in paths:
        try:
            texts[path] = (repo / path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue  # binaries are covered by the size check; deleted files have no text
    return texts


def main(argv: list[str]) -> int:
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel"))
    if argv[:1] == ["--commits"] and len(argv) == 2:
        problems = check_commits(argv[1], repo)
    elif argv[:1] == ["--commit-msg"] and len(argv) == 2:
        lines = Path(argv[1]).read_text(encoding="utf-8").splitlines()
        subject = next((line for line in lines if line and not line.startswith("#")), "")
        problems = check_subject(subject)
    elif not argv:
        sizes = _files(repo)
        paths = sorted(sizes)
        problems = check_paths(paths) + check_contents(_texts(repo, paths)) + check_sizes(sizes)
    else:
        print(__doc__)
        return 2
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
