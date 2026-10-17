"""Fail the build on any dependency whose licence the policy doesn't allow (master plan §2.5).

    uv run python tools/licence_gate.py build/sbom/python.cdx.json [more SBOMs]
    uv run python tools/licence_gate.py --bundle     the third-party bundle

The bundle check (§2.7): every image in deploy/compose/ has deploy/third-party/<name>/ with
LICENSE, NOTICE, VERSION and SOURCE; VERSION's first line is the exact image in use, and
pulled images are pinned by digest.

The policy is master plan Appendix A; changing it is R4's decision, not a code change made
to get a build green. Every licence, and every option of an OR expression, must be allowed
anywhere. (Electing one option of an OR is what ADR-0036 proposes; until R4 accepts it, the
gate stays strict.) A package whose metadata doesn't name an SPDX licence is listed in
tools/licence-review.toml by a person who read its LICENSE file, for that exact version.
A review-required licence passes only for a package an ADR approved, listed under [[approved]]
in tools/licence-review.toml with its exact licence.
"""

import json
import re
import sys
import tomllib
from collections.abc import Collection
from pathlib import Path
from typing import Any

import yaml

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

REVIEWED_FILE = Path(__file__).with_name("licence-review.toml")

REPO = Path(__file__).resolve().parent.parent
COMPOSE_DIR = REPO / "deploy" / "compose"
BUNDLE_DIR = REPO / "deploy" / "third-party"
BUNDLE_FILES = ("LICENSE", "NOTICE", "VERSION", "SOURCE")


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


def own_packages(repo: Path) -> set[str]:
    """The workspace's own packages, read from its pyproject files: 4CE's code carries no
    licence field, so these are skipped. A lookalike name from PyPI is still checked."""
    paths = [repo / "pyproject.toml", *repo.glob("core/*/pyproject.toml")]
    paths += repo.glob("apps/*/pyproject.toml")
    names: set[str] = set()
    for path in paths:
        if path.exists():
            project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
            if "name" in project:
                names.add(normalise(project["name"]))
    return names


def check_components(
    components: list[dict[str, Any]],
    reviewed: dict[tuple[str, str], str],
    own: Collection[str] = frozenset(),
    approved: dict[str, str] | None = None,
) -> list[str]:
    ours = {normalise(name) for name in own}
    approvals = approved or {}
    problems: list[str] = []
    for component in components:
        name, version = component["name"], component.get("version", "")
        key = normalise(name)
        if key in ours or key in COMMERCIAL:
            continue
        texts = (
            [reviewed[(key, version)]] if (key, version) in reviewed else licence_texts(component)
        )
        if not texts:
            problems.append(f"{name} {version}: no licence; read its LICENSE file and record it")
            continue
        if key in approvals and all(text == approvals[key] for text in texts):
            continue
        reasons = [reason for text in texts if (reason := problem(text))]
        if reasons:
            problems.append(f"{name} {version}: {'; '.join(reasons)}")
    return problems


def load_reviewed(text: str) -> dict[tuple[str, str], str]:
    entries = tomllib.loads(text).get("package", [])
    return {(normalise(e["name"]), e["version"]): e["licence"] for e in entries}


def load_approved(text: str) -> dict[str, str]:
    """Packages whose review-required licence an ADR approved, with that exact licence."""
    entries = tomllib.loads(text).get("approved", [])
    return {normalise(e["name"]): e["licence"] for e in entries}


def component(image: str) -> str:
    """The bundle folder for an image: its repository's last path segment, without the tag.
    A registry host may carry a port (localhost:5000/minio), so the tag is cut last."""
    return image.split("@")[0].rsplit("/", 1)[-1].split(":")[0]


BUILT_COMMIT = re.compile(r"^ARG\s+\w+_COMMIT=([0-9a-f]{40})\s*$", re.MULTILINE)


def check_bundle(
    services: dict[str, dict[str, Any]],
    bundle: dict[str, dict[str, str]],
    dockerfiles: dict[str, str] | None = None,
) -> list[str]:
    """Every bundled service ships its licence, notices, exact version and source (§2.7).

    `dockerfiles` maps each built service to its build file, whose `ARG <NAME>_COMMIT=`
    must be the upstream commit that the service's SOURCE records.
    """
    problems: list[str] = []
    used: set[str] = set()
    for service, spec in sorted(services.items()):
        image = spec.get("image", "")
        if not image:
            problems.append(f"{service}: has no image name, so its bundle folder cannot be found")
            continue
        name = component(image)
        used.add(name)
        if "@sha256:" not in image and "build" not in spec:
            problems.append(f"{service}: image {image} is not pinned by digest")
        files = bundle.get(name)
        if files is None:
            problems.append(f"{service}: no deploy/third-party/{name}/ for {image}")
            continue
        missing = [f for f in BUNDLE_FILES if not files.get(f, "").strip()]
        if missing:
            problems.append(f"deploy/third-party/{name}: missing {', '.join(missing)}")
            continue
        if files["VERSION"].splitlines()[0] != image:
            problems.append(f"deploy/third-party/{name}/VERSION: does not name {image}")
        if "build" in spec and dockerfiles is not None:
            commits = BUILT_COMMIT.findall(dockerfiles.get(service, ""))
            if not commits:
                problems.append(f"{service}: its build file records no ARG <NAME>_COMMIT=<sha>")
            problems += [
                f"deploy/third-party/{name}/SOURCE: does not record built commit {c[:8]}"
                for c in commits
                if c not in files["SOURCE"]
            ]
    unused = sorted(set(bundle) - used)
    return problems + [f"deploy/third-party/{n}: no compose service uses it" for n in unused]


def compose_services(directory: Path) -> dict[str, dict[str, Any]]:
    """Every service in the compose files of a folder, overrides merged by service name."""
    services: dict[str, dict[str, Any]] = {}
    for path in sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")]):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for name, spec in document.get("services", {}).items():
            services.setdefault(name, {}).update(spec)
    return services


def _dockerfiles(services: dict[str, dict[str, Any]], directory: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for name, spec in services.items():
        build = spec.get("build")
        if isinstance(build, dict):
            path = directory / build.get("context", ".") / build.get("dockerfile", "Dockerfile")
            files[name] = path.read_text(encoding="utf-8") if path.exists() else ""
    return files


def _bundle() -> dict[str, dict[str, str]]:
    return {
        folder.name: {f.name: f.read_text(encoding="utf-8") for f in folder.iterdir()}
        for folder in sorted(BUNDLE_DIR.glob("*"))
        if folder.is_dir()
    }


def main(argv: list[str]) -> int:
    if argv == ["--bundle"]:
        services = compose_services(COMPOSE_DIR)
        problems = check_bundle(services, _bundle(), _dockerfiles(services, COMPOSE_DIR))
        for line in problems:
            print(line)
        print(f"{len(services)} bundled services checked")
        return 1 if problems else 0
    if not argv:
        print(__doc__)
        return 2
    reviewed = load_reviewed(REVIEWED_FILE.read_text(encoding="utf-8"))
    own = own_packages(REPO)
    approved = load_approved(REVIEWED_FILE.read_text(encoding="utf-8"))
    problems: list[str] = []
    for sbom in argv:
        components = json.loads(Path(sbom).read_text(encoding="utf-8")).get("components", [])
        if not components:
            problems.append(f"{sbom}: no components; was the environment synced?")
        problems += check_components(components, reviewed, own, approved)
        print(f"{sbom}: {len(components)} components checked")
    for line in problems:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
