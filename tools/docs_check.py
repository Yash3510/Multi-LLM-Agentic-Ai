"""Keep docs/ true and connected, as docs/architecture/documentation.md defines.

    uv run python tools/docs_check.py                     every page as it is now
    uv run python tools/docs_check.py --base origin/4ce-core  also the rules for a PR

The PR rules (one work-log entry, drift against `covers`, accepted ADRs unchanged) compare
against --base. --allow-drift skips the drift rule; CI passes it only when the PR carries
the `docs-unaffected` label, which the page owner approves.
"""

import argparse
import posixpath
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import yaml

import repo_check

INDEX = "docs/README.md"
STATE = "docs/state.md"
HISTORY_INDEX = "docs/history/README.md"
STATE_MAX_AGE_DAYS = 7

TYPES = {
    "index",
    "state",
    "glossary",
    "architecture",
    "adr",
    "pack",
    "testing",
    "runbook",
    "log",
    "history",
    "research",
    "assurance",
    "template",
}
STATUSES = {
    "active",
    "implemented",
    "experimental",
    "planned",
    "deprecated",
    "historical",
    "unverified",
}
OWNERS = {"R1", "R2", "R3", "R4"}
DECISION_STATUSES = {"proposed", "accepted", "superseded"}
REQUIRED = ("title", "type", "status", "owner", "updated", "tags")
TYPE_FIELDS = {
    "adr": ("number", "decision_status", "superseded_by"),
    "log": ("date", "branch", "pr", "work_package", "author", "areas"),
    "history": ("commits",),
}
# What may change in an accepted ADR: only marking it superseded.
ADR_MUTABLE = {"superseded_by", "decision_status", "status", "updated"}

FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
TAG_LINE = re.compile(r"^- `([^`]+)`\s*$")


def split(text: str) -> tuple[dict[str, Any] | None, str]:
    """Return (frontmatter, body). Frontmatter is None if missing or not valid YAML."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return None, text
    return (meta if isinstance(meta, dict) else None), text[end + 5 :]


def allowed_tags(index_text: str) -> set[str]:
    _, body = split(index_text)
    section = body.split("\n## Tags", 1)[-1].split("\n## ", 1)[0]
    return {m.group(1) for line in section.splitlines() if (m := TAG_LINE.match(line))}


def check_frontmatter(pages: dict[str, str]) -> list[str]:
    tags = allowed_tags(pages.get(INDEX, ""))
    problems: list[str] = []
    for path, text in sorted(pages.items()):
        meta, _ = split(text)
        if meta is None:
            problems.append(f"{path}: no frontmatter")
            continue
        missing = [field for field in REQUIRED if field not in meta]
        problems += [f"{path}: missing '{field}'" for field in missing]
        if path.startswith("docs/templates/") and not path.endswith("/README.md"):
            continue  # a template's values are placeholders
        problems += [f"{path}: {p}" for p in _value_problems(path, meta, tags)]
    return problems


def _value_problems(path: str, meta: dict[str, Any], tags: set[str]) -> list[str]:
    problems: list[str] = []
    if "type" in meta and meta["type"] not in TYPES:
        problems.append(f"type '{meta['type']}' is not one of the allowed types")
    if "status" in meta and meta["status"] not in STATUSES:
        problems.append(f"status '{meta['status']}' is not one of the allowed statuses")
    if "owner" in meta and meta["owner"] not in OWNERS:
        problems.append(f"owner '{meta['owner']}' is not R1, R2, R3 or R4")
    if "updated" in meta and not isinstance(meta["updated"], date):
        problems.append("'updated' is not a YYYY-MM-DD date")
    unknown = [t for t in meta.get("tags") or [] if t not in tags]
    problems += [f"tag '{t}' is not in the list in {INDEX}" for t in unknown]
    covers = meta.get("covers", [])
    if not isinstance(covers, list) or not all(isinstance(c, str) for c in covers):
        problems.append("'covers' is not a list of paths")
    for field in TYPE_FIELDS.get(meta.get("type", ""), ()):
        if field not in meta:
            problems.append(f"a {meta['type']} page needs '{field}'")
    if meta.get("type") == "adr" and meta.get("decision_status") not in DECISION_STATUSES:
        problems.append(f"decision_status '{meta.get('decision_status')}' is not allowed")
    if path == HISTORY_INDEX and "last_processed_commit" not in meta:
        problems.append("the history index needs 'last_processed_commit'")
    return problems


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "").lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def _anchors(text: str) -> set[str]:
    _, body = split(text)
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    for match in HEADING.finditer(FENCE.sub("", body)):
        base = slug(match.group(1))
        count = seen.get(base, 0)
        anchors.add(base if count == 0 else f"{base}-{count}")
        seen[base] = count + 1
    return anchors


def _links(path: str, text: str) -> list[tuple[str, str, str]]:
    """(raw link, resolved repo path, anchor) for every relative link outside code."""
    _, body = split(text)
    prose = INLINE_CODE.sub("", FENCE.sub("", body))
    found: list[tuple[str, str, str]] = []
    for match in LINK.finditer(prose):
        raw = match.group(1)
        if re.match(r"[a-z][a-z0-9+.-]*:", raw):
            continue  # http:, https:, mailto:
        target, _, anchor = raw.partition("#")
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target or ""))
        found.append((raw, path if not target else resolved, anchor))
    return found


def check_links(pages: dict[str, str], exists: Callable[[str], bool]) -> list[str]:
    problems: list[str] = []
    for path, text in sorted(pages.items()):
        for raw, target, anchor in _links(path, text):
            if target in pages:
                if anchor and anchor not in _anchors(pages[target]):
                    problems.append(f"{path}: link '{raw}' has no such heading")
            elif not exists(target):
                problems.append(f"{path}: link '{raw}' points to nothing")
    return problems


def check_orphans(pages: dict[str, str]) -> list[str]:
    reached = {INDEX}
    queue = [INDEX]
    while queue:
        page = queue.pop()
        for _, target, _ in _links(page, pages.get(page, "")):
            if target in pages and target not in reached:
                reached.add(target)
                queue.append(target)
    return [f"{p}: not reachable from {INDEX}" for p in sorted(pages) if p not in reached]


def check_state(pages: dict[str, str], today: date) -> list[str]:
    meta, _ = split(pages.get(STATE, ""))
    updated = (meta or {}).get("updated")
    if not isinstance(updated, date):
        return [f"{STATE}: no 'updated' date"]
    age = (today - updated).days
    if age > STATE_MAX_AGE_DAYS:
        return [f"{STATE}: last updated {age} days ago; update it at least weekly"]
    return []


def check_work_log(added: list[str]) -> list[str]:
    entries = [p for p in added if p.startswith("docs/log/") and not p.endswith("README.md")]
    if len(entries) == 1:
        return []
    found = ", ".join(entries) or "none"
    return [f"docs/log/: a PR adds exactly one work-log entry; found {found}"]


def _covered(path: str, cover: str) -> bool:
    return path.startswith(cover) if cover.endswith("/") else path == cover


def check_covers(
    pages: dict[str, str], exists: Callable[[str], bool], is_dir: Callable[[str], bool]
) -> list[str]:
    """A page's `covers` must name real paths, folders with a trailing /, or drift goes quiet.
    A planned page may cover what isn't built yet."""
    problems: list[str] = []
    for page, text in sorted(pages.items()):
        meta, _ = split(text)
        if meta is None or meta.get("status") == "planned" or page.startswith("docs/templates/"):
            continue
        for cover in meta.get("covers") or []:
            if not exists(cover):
                problems.append(f"{page}: covers {cover}, which doesn't exist")
            elif is_dir(cover) and not cover.endswith("/"):
                problems.append(f"{page}: covers the folder {cover}; write it with a trailing /")
    return problems


def check_drift(pages: dict[str, str], changed: list[str]) -> list[str]:
    """Pages whose covered code changed in this PR without the page changing too. ADRs are
    records that are never edited once accepted, so they never drift."""
    problems: list[str] = []
    for page, text in sorted(pages.items()):
        meta, _ = split(text)
        if meta is None or page in changed or meta.get("type") == "adr":
            continue
        for cover in meta.get("covers") or []:
            if any(_covered(path, cover) for path in changed):
                problems.append(f"{page}: covers {cover} which changed; update the page")
    return problems


def check_history(pages: dict[str, str], processed: list[str]) -> list[str]:
    listed: dict[str, list[str]] = {}
    for page, text in pages.items():
        meta, _ = split(text)
        if page.startswith("docs/history/") and meta and meta.get("type") == "history":
            for short in meta.get("commits") or []:
                listed.setdefault(str(short), []).append(page)
    problems: list[str] = []
    for commit in processed:
        pages_with = [p for short, ps in listed.items() if commit.startswith(short) for p in ps]
        if not pages_with:
            problems.append(f"{commit[:7]}: in no milestone page")
        elif len(pages_with) > 1:
            problems.append(f"{commit[:7]}: in more than one milestone ({', '.join(pages_with)})")
    return problems


def check_adrs(pages: dict[str, str], base: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for path, old_text in sorted(base.items()):
        old_meta, old_body = split(old_text)
        if old_meta is None or old_meta.get("decision_status") != "accepted":
            continue
        new_meta, new_body = split(pages.get(path, ""))
        new_meta = new_meta or {}
        changed = {k for k in {*old_meta, *new_meta} if new_meta.get(k) != old_meta.get(k)}
        if new_body != old_body or changed - ADR_MUTABLE:
            problems.append(f"{path}: an accepted ADR is never edited; write a new one")
        elif changed and not (
            new_meta.get("decision_status") == "superseded" and new_meta.get("superseded_by")
        ):
            problems.append(
                f"{path}: an accepted ADR only changes to superseded, naming its successor"
            )
    return problems


def _git(repo: Path, *args: str) -> str:
    command = ["git", "-C", str(repo), *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def _docs_pages(repo: Path) -> dict[str, str]:
    listing = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "docs")
    paths = [p for p in listing.split("\0") if p.endswith(".md") and (repo / p).exists()]
    return {p: (repo / p).read_text(encoding="utf-8") for p in paths}


def _processed_commits(repo: Path, pages: dict[str, str]) -> list[str]:
    meta, _ = split(pages.get(HISTORY_INDEX, ""))
    last = (meta or {}).get("last_processed_commit")
    return _git(repo, "rev-list", str(last)).split() if last else []


def pr_problems(repo: Path, base: str, allow_drift: bool = False) -> list[str]:
    """The rules for a PR into `base`: one log entry, no drift, accepted ADRs untouched.
    --no-renames lists a moved file under its old path too, so moving covered code drifts."""
    span = f"{base}...HEAD"
    changed = _git(repo, "diff", "--name-only", "--no-renames", span).split()
    added = _git(repo, "diff", "--name-only", "--no-renames", "--diff-filter=A", span).split()
    adr_paths = _git(repo, "ls-tree", "-r", "--name-only", base, "--", "docs/adr/").split()
    base_adrs = {p: _git(repo, "show", f"{base}:{p}") for p in adr_paths}
    pages = _docs_pages(repo)
    problems = check_work_log(added)
    if not allow_drift:
        problems += check_drift(pages, changed)
    return problems + check_adrs(pages, base_adrs)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check docs/ against the documentation rules.")
    parser.add_argument("--base", help="the branch a PR targets, e.g. origin/4ce-core")
    parser.add_argument("--allow-drift", action="store_true", help="the docs-unaffected label")
    args = parser.parse_args(argv)
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    pages = _docs_pages(repo)
    problems = check_frontmatter(pages)
    problems += check_links(pages, lambda p: (repo / p).exists())
    problems += check_covers(pages, lambda p: (repo / p).exists(), lambda p: (repo / p).is_dir())
    problems += check_orphans(pages)
    problems += [p for p in repo_check.check_paths(list(pages)) if p.startswith("docs/")]
    problems += check_state(pages, date.today())
    problems += check_history(pages, _processed_commits(repo, pages))
    if args.base:
        problems += pr_problems(repo, args.base, args.allow_drift)
    else:
        print("no --base given: skipped the work-log, drift and ADR rules", file=sys.stderr)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
