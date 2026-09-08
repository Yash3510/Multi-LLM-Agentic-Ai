"""
Exercise every 4CE tool against the real runtime.

    cd backend && ../.venv/Scripts/python.exe ../4ce/test_tools.py

Run it from the backend directory so the open_webui package and its database
resolve. Each tool is loaded from source the same way the application loads it,
then driven through its success and failure paths. Prints a pass/fail summary
and exits non-zero if anything fails, so it can gate a demo-day check.
"""

import asyncio
import glob
import importlib.util
import os
import sqlite3
import sys
import zipfile
from pathlib import Path

# Running this script puts its own directory on sys.path, not the working
# directory, so the backend package would not resolve without this.
sys.path.insert(0, os.getcwd())

TOOLS = Path(__file__).resolve().parent / "tools"
RESULTS: list[tuple[str, bool, str]] = []


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Tools()


def check(label: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))


def admin_user_id() -> str | None:
    matches = glob.glob("data/webui.db")
    if not matches:
        return None
    row = sqlite3.connect(matches[0]).execute("select id from user limit 1").fetchone()
    return row[0] if row else None


async def test_sandbox() -> None:
    print("\n4CE Sovereign Sandbox")
    tool = load("sandbox")

    out = await tool.run_python("print('hello'); print(6*7)")
    check("executes code and returns stdout", "42" in out and "completed" in out)

    out = await tool.run_python(
        "import urllib.request\n"
        "try:\n"
        "    urllib.request.urlopen('https://example.com', timeout=5)\n"
        "    print('REACHABLE')\n"
        "except Exception as exc:\n"
        "    print('blocked:', type(exc).__name__)"
    )
    check("outbound network is blocked", "REACHABLE" not in out and "blocked:" in out)

    out = await tool.run_python("raise ValueError('boom')")
    check("non-zero exit reported as failed", "failed" in out and "ValueError" in out)

    out = await tool.run_python("open('/workspace/x','w')")
    check("workspace mount is read-only", "failed" in out)

    original = tool.valves.timeout_seconds
    tool.valves.timeout_seconds = 5
    out = await tool.run_python("import time; time.sleep(30)")
    check("wall-clock timeout enforced", "Timed out" in out or "time limit" in out)
    tool.valves.timeout_seconds = original

    out = await tool.run_python("   ")
    check("empty source rejected", "No code" in out)


async def test_deliverables() -> None:
    print("\n4CE Deliverables")
    tool = load("deliverables")
    uid = admin_user_id()
    if not uid:
        check("admin user available", False, "no user row found; run from backend/")
        return

    out = await tool.create_word_document(
        "Approval Note - Pump P-101B",
        "## Scope\n\nRoutine inspection.\n\n## Findings\n\n- Seal weeping 3-4 dpm\n- Vibration Zone B\n\n"
        "## Recommendation\n\nApprove return to service.",
        "MIR/2026/0431",
        __user__={"id": uid},
    )
    ok = "Download" in out and ".docx" in out
    check("generates a .docx and returns a link", ok, out.splitlines()[0][:70] if not ok else "")

    if ok:
        newest = max(glob.glob("data/uploads/*.docx"), key=lambda p: Path(p).stat().st_mtime)
        with zipfile.ZipFile(newest) as archive:
            names = archive.namelist()
            body = archive.read("word/document.xml").decode("utf-8", "replace")
        check("file is a valid OOXML package", "word/document.xml" in names)
        check("content is present in the document", "P-101B" in body and "Recommendation" in body)
        check("classification banner applied", "CONFIDENTIAL" in body)

    out = await tool.create_word_document("Title", "   ", __user__={"id": uid})
    check("empty body rejected", "empty" in out.lower())

    out = await tool.create_word_document("", "content", __user__={"id": uid})
    check("missing title rejected", "title is required" in out.lower())

    out = await tool.create_word_document("Title", "content", __user__=None)
    check("unattributed request rejected", "not generated" in out.lower())


async def test_sovereignty() -> None:
    print("\n4CE Sovereignty Check")
    tool = load("sovereignty")

    out = await tool.verify_sovereignty()
    check("produces an audit table", "Sovereignty audit" in out and "| Surface |" in out)
    check("reports a verdict", "PASS" in out or "ATTENTION REQUIRED" in out)
    check("states its own limitation", "does not observe packets" in out)

    ok_local = tool._is_local("http://localhost:1234/v1") and tool._is_local("http://127.0.0.1:8080")
    check("classifies loopback as on-premise", ok_local)
    check("classifies private ranges as on-premise", tool._is_local("http://192.168.1.50:11434"))
    check("classifies public hosts as external", not tool._is_local("https://api.openai.com/v1"))


async def main() -> None:
    if not Path("data").exists():
        print("Run this from the backend/ directory so open_webui and its database resolve.")
        sys.exit(2)

    await test_sandbox()
    await test_deliverables()
    await test_sovereignty()

    failed = [label for label, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("Failed: " + "; ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
