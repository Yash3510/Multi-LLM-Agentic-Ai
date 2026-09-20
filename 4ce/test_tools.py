"""
Exercise every 4CE tool against the real runtime.

    cd backend && ../.venv/bin/python ../4ce/test_tools.py           # macOS, Linux
    cd backend && ../.venv/Scripts/python.exe ../4ce/test_tools.py   # Windows

Run it from the backend directory so the open_webui package and its database
resolve. Each tool is loaded from source the same way the application loads it,
then driven through its success and failure paths. Prints a pass/fail summary
and exits non-zero if anything fails, so it can gate a demo-day check.
"""

import asyncio
import glob
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
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

    # Files are how a run hands back a spreadsheet or a chart. /output is the only
    # writable path that survives, and a configured directory keeps a copy on disk.
    with tempfile.TemporaryDirectory(prefix="4ce-test-out-") as keep:
        tool.valves.output_dir = keep
        out = await tool.run_python(
            "open('/output/readings.csv','w').write('a,b'); print('done')"
        )
        check(
            "files written to /output are returned",
            "completed" in out and "Files produced" in out and "readings.csv" in out,
        )
        landed = Path(keep) / "readings.csv"
        check("returned files reach the configured directory", landed.is_file())
        check(
            "the returned file holds what the run wrote",
            landed.is_file() and landed.read_text() == "a,b",
        )

    out = await tool.run_python("print('no files here')")
    check("a run producing no files says so", "Files produced" not in out)

    original_cap = tool.valves.max_output_file_mb
    tool.valves.max_output_file_mb = 0
    out = await tool.run_python("open('/output/big.bin','wb').write(b'x'*2048); print('ok')")
    check("an oversized file is refused, not silently dropped", "Not returned" in out)
    tool.valves.max_output_file_mb = original_cap


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


DEMO_REPORT = """1.2  Mechanical seal exhibits intermittent weeping, approximately 3 to 4 drops
     per minute during sustained operation.
1.3  Bearing housing temperature recorded at 71 degrees C against an alarm limit of 80 degrees C.
1.4  Vibration measured at 4.1 mm/s RMS. ISO 10816 Zone B.
1.5  Coupling guard fastener missing at position 3 of 4.
Minimum measured wall thickness: 11.2 mm (nominal 12.7 mm)
Retirement thickness: 9.5 mm
"""


async def test_sop_check() -> None:
    print("\n4CE SOP Threshold Check")
    tool = load("sop_check")

    out = await tool.check_sop_thresholds(DEMO_REPORT)
    check("produces an assessment table", "SOP assessment" in out and "| Parameter |" in out)
    check("seal leakage 3-4 dpm passes on 2.1", "| Seal leakage | 3 to 4 drops/min" in out and "§2.1 | PASS" in out)
    check("vibration Zone B passes on 3.1", "| Zone B |" in out and "§3.1 | PASS" in out)
    check("wall thickness margin computed", "1.7 mm margin" in out)
    check("thin margin raises the 4.2 action", "**§4.2**" in out and "six months" in out)
    check("missing guard fastener fails on 5.1", "§5.1 | FAIL" in out)
    check("blocks the start on a 5.1 failure", "Disposition: NOT FIT FOR START" in out)
    check("unassessed readings are listed", "Readings outside this SOP" in out and "Bearing housing" in out)

    out = await tool.check_sop_thresholds("Seal leakage 12 drops per minute.")
    check("12 dpm requires review under 2.2", "§2.2 | REVIEW" in out and "30 days" in out)

    out = await tool.check_sop_thresholds("Seal leakage 25 drops per minute.")
    check("25 dpm fails under 2.3", "§2.3 | FAIL" in out and "REMOVE FROM SERVICE" in out)

    out = await tool.check_sop_thresholds("Seal leakage 3 to 25 drops per minute.")
    check("a range is assessed at its worse end", "§2.3 | FAIL" in out)

    out = await tool.check_sop_thresholds("Vibration ISO 10816 Zone D.")
    check("Zone D fails under 3.3", "§3.3 | FAIL" in out)

    out = await tool.check_sop_thresholds(
        "Minimum measured wall thickness 9.1 mm. Retirement thickness 9.5 mm."
    )
    check("thickness below retirement fails under 4.1", "§4.1 | FAIL" in out and "-0.4 mm margin" in out)

    out = await tool.check_sop_thresholds("Seal shows atomised spray at the gland.")
    check("atomised spray fails under 2.3", "Seal atomisation" in out and "§2.3 | FAIL" in out)

    out = await tool.check_sop_thresholds("Inspector attended site. Vibration ISO 10816 Zone A.")
    check("an absent reading is NO DATA, not PASS", "| Seal leakage | not found" in out and "NO DATA" in out)
    check("incomplete assessment does not read as fit", "Disposition: ASSESSMENT INCOMPLETE" in out)

    out = await tool.check_sop_thresholds("   ")
    check("empty input rejected", "No readings were supplied" in out)

    broken = load("sop_check")
    broken.valves.rule_pack = "{not json"
    out = await broken.check_sop_thresholds("Seal leakage 3 drops per minute.")
    check("malformed rule pack reported, not ignored", "could not be read" in out and "No assessment" in out)

    custom = load("sop_check")
    custom.valves.rule_pack = json.dumps({
        "sop_id": "SOP-ELE-002",
        "rules": [{
            "id": "ir", "parameter": "Insulation resistance", "unit": "MOhm", "type": "band",
            "limit": "above 50 MOhm",
            "patterns": [r"insulation resistance[^0-9]{0,20}(\d+(?:\.\d+)?)"],
            "bands": [
                {"max": 50, "verdict": "FAIL", "clause": "3.1", "action": "Do not energise.",
                 "disposition": "REMOVE FROM SERVICE"},
                {"verdict": "PASS", "clause": "3.2", "disposition": "FIT FOR SERVICE"},
            ],
        }],
    })
    out = await custom.check_sop_thresholds("Insulation resistance 22 MOhm measured at 500 V.")
    check("a custom rule pack drives the engine", "SOP-ELE-002" in out and "§3.1 | FAIL" in out)

    out = await tool.check_sop_thresholds(DEMO_REPORT)
    check("states its own limitation", "only for the parameters in its rule pack" in out)


async def main() -> None:
    if not Path("data").exists():
        print("Run this from the backend/ directory so open_webui and its database resolve.")
        sys.exit(2)

    await test_sandbox()
    await test_deliverables()
    await test_sovereignty()
    await test_sop_check()

    failed = [label for label, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("Failed: " + "; ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
