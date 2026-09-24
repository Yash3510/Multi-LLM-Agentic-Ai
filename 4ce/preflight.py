"""
Check that a machine is actually ready to run 4CE, and say what is not.

    python 4ce/preflight.py             report only
    python 4ce/preflight.py --fix       also load the models the way 4CE needs

Run this before a demo. Every check here exists because it failed once and cost
real time to diagnose.

The model context length is the one worth understanding. Bionic remembers a
context length per model and will happily reload a 4B model at 65,536 tokens.
On a 6 GB card that key/value cache does not fit, the runtime spills it to
system memory, and generation drops to a crawl - a vision task that takes two
minutes at 8192 took over twenty. Nothing reports an error; it is simply slow.
The same applies to the idle TTL: a model that unloads after an hour gets
reloaded mid-demo, and because ULTRON deliberately runs on a different model
from JARVIS, an evicted model means a reload on nearly every turn.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MODEL_SERVER = "http://127.0.0.1:1234"
# Default only; --base overrides it, so a second instance can be checked
# without editing this file.
DEFAULT_BACKEND = "http://127.0.0.1:8080"
SANDBOX_IMAGE = "python:3.12-alpine"

# Context length 4CE loads these at. Larger is not better here: it is slower.
MAX_CONTEXT = 8192
# The models the router chooses between, and the context each is loaded at,
# from the same registry the router reads.
REGISTRY = json.loads((ROOT / "models.json").read_text(encoding="utf-8"))
REQUIRED_MODELS = tuple(m["id"] for m in REGISTRY["models"])
CONTEXTS = {m["id"]: m.get("context") for m in REGISTRY["models"]}
EMBEDDING_MODEL = REGISTRY["embedding"]["id"]

TOOL_IDS = ("ace_sandbox", "ace_deliverables", "ace_sovereignty", "ace_sop_check", "ace_calculations")
FUNCTION_ID = "ace_orchestrator"

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"

# Decode subprocess output as UTF-8 regardless of the console code page.
# On a cp1252 console the default decode raises inside subprocess's reader
# thread, printing a traceback above a report that otherwise passes.
_TEXT = {"encoding": "utf-8", "errors": "replace"}


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, state: str, name: str, detail: str = "") -> None:
        self.rows.append((state, name, detail))

    def render(self) -> int:
        width = max(len(name) for _, name, _ in self.rows)
        for state, name, detail in self.rows:
            print(f"  {state:<4}  {name.ljust(width)}  {detail}")
        failures = sum(1 for state, _, _ in self.rows if state == FAIL)
        warnings = sum(1 for state, _, _ in self.rows if state == WARN)
        print()
        if failures:
            print(f"{failures} check(s) failed. 4CE will not demo correctly until they pass.")
        elif warnings:
            print(f"Ready, with {warnings} warning(s) worth reading.")
        else:
            print("Ready.")
        return 1 if failures else 0


def get_json(url: str, token: str | None = None, timeout: int = 10):
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def post_json(url: str, payload: dict, token: str | None = None, timeout: int = 30):
    request = urllib.request.Request(url, data=json.dumps(payload).encode())
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def find_lms() -> str | None:
    """The model server's CLI, which is not usually on PATH.

    Bionic is the rebranded successor to LM Studio and kept the old names
    on disk, so the binary is still `lms` under a `.lmstudio` directory.
    """
    found = shutil.which("lms")
    if found:
        return found
    candidates = [
        Path.home() / ".lmstudio" / "bin" / "lms.exe",
        Path.home() / ".lmstudio" / "bin" / "lms",
        Path(os.environ.get("LOCALAPPDATA", "")) / "LM-Studio" / "lms.exe",
    ]
    return next((str(p) for p in candidates if p.is_file()), None)


def load_model(lms: str, model: str, context: int | None) -> tuple[bool, str]:
    command = [lms, "load", model, "--gpu", "max", "-y"]
    if context:
        command += ["-c", str(context)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=600, **_TEXT)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip().splitlines()[-1:][0] if (result.stderr or result.stdout).strip() else "load failed"
    return True, "loaded"


def check_models(report: Report, fix: bool) -> None:
    try:
        models = get_json(f"{MODEL_SERVER}/api/v0/models")["data"]
    except Exception as exc:
        report.add(FAIL, "Model server", f"{MODEL_SERVER} unreachable ({exc}). Start Bionic's server.")
        return

    by_id = {m.get("id"): m for m in models}
    lms = find_lms()

    for model in (*REQUIRED_MODELS, EMBEDDING_MODEL):
        entry = by_id.get(model)
        wanted = None if model == EMBEDDING_MODEL else (CONTEXTS.get(model) or MAX_CONTEXT)

        if entry is None:
            report.add(FAIL, model, "not installed in Bionic")
            continue

        loaded = entry.get("state") == "loaded"
        context = entry.get("loaded_context_length")
        too_big = bool(wanted and loaded and context and context > wanted)

        if loaded and not too_big:
            report.add(PASS, model, f"loaded{f' at {context}' if context else ''}")
            continue

        why = f"loaded at {context}, which will not fit in VRAM" if too_big else "not loaded"
        if not fix:
            hint = "re-run with --fix" if lms else "install the Bionic CLI, or load it in the app"
            report.add(FAIL, model, f"{why} - {hint}")
            continue
        if not lms:
            report.add(FAIL, model, f"{why} - Bionic CLI not found, load it in the app")
            continue

        if too_big:
            subprocess.run([lms, "unload", model], capture_output=True, text=True, **_TEXT)
        ok, detail = load_model(lms, model, wanted)
        report.add(PASS if ok else FAIL, model, f"reloaded at {wanted}" if ok and wanted else detail)


def check_docker(report: Report) -> None:
    if not shutil.which("docker"):
        report.add(FAIL, "Docker", "not on PATH - the sandbox cannot run")
        return
    probe = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True, **_TEXT)
    if probe.returncode != 0:
        report.add(FAIL, "Docker", "daemon not responding - start Docker Desktop")
        return
    report.add(PASS, "Docker", f"engine {probe.stdout.strip()}")

    images = subprocess.run(
        ["docker", "images", SANDBOX_IMAGE, "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True, text=True, **_TEXT,
    )
    if SANDBOX_IMAGE in images.stdout:
        report.add(PASS, "Sandbox image", SANDBOX_IMAGE)
    else:
        report.add(FAIL, "Sandbox image", f"{SANDBOX_IMAGE} missing - run: docker pull {SANDBOX_IMAGE}")


def check_backend(report: Report, backend: str, email: str, password: str) -> None:
    try:
        get_json(f"{backend}/health")
    except Exception:
        report.add(FAIL, "Backend", f"{backend} unreachable - start it before demoing")
        return
    report.add(PASS, "Backend", backend)

    try:
        token = post_json(f"{backend}/api/v1/auths/signin", {"email": email, "password": password})["token"]
    except Exception:
        report.add(FAIL, "Admin sign-in", f"{email} rejected - run 4ce/install.py first")
        return
    report.add(PASS, "Admin sign-in", email)

    try:
        installed = {t["id"] for t in get_json(f"{backend}/api/v1/tools/", token)}
    except Exception:
        installed = set()
    missing = [t for t in TOOL_IDS if t not in installed]
    if missing:
        report.add(FAIL, "Tools installed", f"missing {', '.join(missing)} - run 4ce/install.py")
    else:
        report.add(PASS, "Tools installed", f"{len(TOOL_IDS)} of {len(TOOL_IDS)}")

    served = [m.get("id", "") for m in get_json(f"{backend}/api/models", token).get("data", [])]
    model_id = next((m for m in served if m.startswith(FUNCTION_ID + ".")), None)
    if not model_id:
        report.add(FAIL, "Orchestrator model", "not served - run 4ce/install.py")
        return
    report.add(PASS, "Orchestrator model", model_id)

    record = get_json(f"{backend}/api/v1/models/model?id={model_id}", token) or {}
    attached = (record.get("meta") or {}).get("toolIds") or []
    if sorted(attached) == sorted(TOOL_IDS):
        report.add(PASS, "Tools attached", f"the chain can call all {len(TOOL_IDS)}")
    else:
        report.add(
            FAIL,
            "Tools attached",
            "the chain will reason unaided - run 4ce/install.py",
        )

    check_knowledge(report, backend, record, token)
    check_egress(report, backend, token)

    try:
        valves = get_json(f"{backend}/api/v1/functions/id/{FUNCTION_ID}/valves", token) or {}
    except Exception:
        valves = {}
    if valves.get("require_approval") is False:
        report.add(WARN, "Approval gate", "disabled in valves - nothing will be withheld")
    else:
        report.add(PASS, "Approval gate", "on")

    audio = get_json(f"{backend}/api/v1/audio/config", token)
    engine = (audio.get("stt") or {}).get("ENGINE") or ""
    if engine == "":
        cached = (ROOT.parent / "backend" / "data" / "cache" / "whisper" / "models").exists()
        if cached:
            report.add(PASS, "Speech to text", "local whisper, weights cached")
        else:
            report.add(WARN, "Speech to text", "local whisper but no cached weights - the microphone will fail offline")
    else:
        report.add(WARN, "Speech to text", f"engine '{engine}' - check it does not leave the machine")


def check_knowledge(report: Report, backend: str, record: dict, token: str) -> None:
    """Whether the chain can still be grounded in the plant's own documents.

    Nothing errors when this breaks. Retrieval returns nothing, the agents
    answer from the model's own memory, and the reply still reads like an
    informed one - which is the failure this system exists to make visible, so
    it is the last one that should go unnoticed until a demonstration.

    Two ways it has broken here. The knowledge base can end up detached from
    the model, and the admin "Reset vector DB" action deletes every knowledge
    record along with the vectors - after which reindexing reports success and
    rebuilds nothing, because there is no longer a record to reindex.
    """
    attached = (record.get("meta") or {}).get("knowledge") or []
    if not attached:
        report.add(
            FAIL,
            "Knowledge attached",
            "no knowledge base on the model - the chain cannot be grounded",
        )
        return

    names, broken = [], []
    for item in attached:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("id") or "?"
        names.append(name)
        try:
            detail = get_json(f"{backend}/api/v1/knowledge/{item.get('id')}", token) or {}
        except Exception:
            detail = {}
        if detail.get("name") is None:
            broken.append(f"{name} (record missing)")

    if broken:
        report.add(
            FAIL,
            "Knowledge attached",
            f"{', '.join(broken)} - see 'Recovering retrieval' in 4ce/docs/HOW_TO_RUN.md",
        )
    else:
        report.add(PASS, "Knowledge attached", ", ".join(names))


def check_egress(report: Report, backend: str, token: str) -> None:
    """Whether the egress watch is observing, and what it has seen so far.

    The Sovereignty page and every run's receipt report what this watch
    counts. When it is not sampling they say "not observed" - honest, but a
    sovereignty demonstration without observation is back to being a claim.
    """
    try:
        egress = get_json(f"{backend}/api/v1/fource/egress", token) or {}
    except Exception:
        report.add(FAIL, "Egress watch", "not served - the backend predates it or it failed to start")
        return
    if not egress.get("running"):
        report.add(FAIL, "Egress watch", "not running - restart the backend")
        return

    flows = egress.get("flows") or {}
    external, lan_out = flows.get("external", 0), flows.get("lan_out", 0)
    if external or lan_out:
        events = (egress.get("external") or []) + (egress.get("lan_out") or [])
        seen = ", ".join(sorted({f"{e['process']} to {e['remote']}" for e in events})[:3])
        report.add(
            WARN, "Egress watch",
            f"{external} external, {lan_out} LAN outbound seen ({seen}) - the monitor will not "
            "read zero. See the Sovereignty page, then start a new window",
        )
    else:
        processes = len(egress.get("scope") or [])
        report.add(PASS, "Egress watch", f"sampling {processes} processes, nothing has left the machine")

    canaries = egress.get("canaries") or []
    if canaries and canaries[0].get("outcome") == "reachable":
        report.add(
            WARN, "Egress rule",
            "the canary reached the internet - nothing on this host blocks egress. "
            "See 'Making it physical' in 4ce/docs/HOW_TO_RUN.md",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a machine is ready to run 4CE.")
    parser.add_argument("--fix", action="store_true", help="load the models 4CE needs, at the context length it needs")
    parser.add_argument("--base", default=DEFAULT_BACKEND,
                        help="the 4CE backend to check, e.g. http://127.0.0.1:8081")
    parser.add_argument("--email", default="admin@4ce.local")
    parser.add_argument("--password", default="4ce-demo-password")
    args = parser.parse_args()

    print("\n4CE preflight\n")
    report = Report()
    check_models(report, args.fix)
    check_docker(report)
    check_backend(report, args.base.rstrip("/"), args.email, args.password)
    sys.exit(report.render())


if __name__ == "__main__":
    main()
