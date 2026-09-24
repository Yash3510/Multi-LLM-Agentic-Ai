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
    # Nothing is watching egress in this process yet: the report must say so,
    # not print a verdict that sounds observed.
    check("says when egress was not observed", "PASS on configuration, not observed" in out
          or "ATTENTION REQUIRED" in out)
    check("states its own limitation", "rests on configuration alone" in out)

    from open_webui.utils.fource_egress import watch
    watch.set_endpoints(["http://127.0.0.1:1234/v1"])
    watch.start()
    await asyncio.sleep(0.8)
    try:
        out = await tool.verify_sovereignty()
        check("reports what the workbench was observed doing",
              "What the workbench actually did" in out and "samples" in out)
        check("states what sampling cannot see", "not by capturing packets" in out)
    finally:
        watch.stop()

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


async def test_egress() -> None:
    """The egress watch's classification, against a socket table it is handed.

    Synthetic, so it is deterministic and makes no connection of its own: the
    point is that each kind of flow lands in the right count, once.
    """
    print("\n4CE Egress watch")
    from collections import namedtuple

    import psutil
    import open_webui.utils.fource_egress as egress

    conn = namedtuple("conn", "fd family type laddr raddr status pid")
    addr = namedtuple("addr", "ip port")
    me, model = os.getpid(), 999_001

    def c(local, remote, status="ESTABLISHED", pid=me):
        return conn(-1, 2, 1, addr(*local), addr(*remote) if remote else (), status, pid)

    table: list = []
    listening = [
        c(("127.0.0.1", 8080), None, psutil.CONN_LISTEN),
        c(("127.0.0.1", 1234), None, psutil.CONN_LISTEN, model),
    ]
    real_table, real_family = egress.psutil.net_connections, egress._family
    egress.psutil.net_connections = lambda kind="inet": listening + table
    egress._family = lambda pid: {pid: ("backend.exe" if pid == me else "model.exe", "")} \
        if pid in (me, model) else {}
    try:
        w = egress.EgressWatch()
        w.set_endpoints(["http://127.0.0.1:1234/v1", "http://192.168.1.50:8000/v1"])

        def sample(*flows):
            table[:] = list(flows)
            w._sample()

        sample(c(("127.0.0.1", 50001), ("127.0.0.1", 1234)))
        sample(c(("127.0.0.1", 50001), ("127.0.0.1", 1234)))
        check("a loopback flow is counted once across samples", w.flows["local"] == 1)
        check("the model server is in scope by its port",
              {m["role"] for m in w._scope.values()} == {"backend", "model server"})

        sample(c(("192.168.1.9", 8080), ("192.168.1.20", 61000)))
        sample(c(("192.168.1.9", 50100), ("192.168.1.50", 8000)))
        check("LAN clients and the configured LAN endpoint are not leaks",
              w.flows["lan_in"] == 1 and w.flows["lan_expected"] == 1 and w.flows["lan_out"] == 0)

        mark = w.mark()
        sample(c(("192.168.1.9", 50200), ("192.168.1.77", 3128)))
        sample(c(("10.0.0.5", 50300), ("93.184.216.34", 443), pid=model))
        event = next(iter(w._events["external"].values()))
        check("other outbound LAN and the internet are flagged",
              w.flows["lan_out"] == 1 and w.flows["external"] == 1)
        check("an external flow names the process that made it", event["role"] == "model server")
        check("a run is not reported as observed when nothing was watching",
              w.since_mark(mark)["observed"] is False)

        w._thread = type("Alive", (), {"is_alive": lambda self: True})()
        run = w.since_mark(mark)
        check("a watched run reports what happened during it",
              run["observed"] and run["external"] == 1 and run["lan_out"] == 1)

        import time as _time
        w._canary = ("1.1.1.1", 443, _time.time() + 5)
        sample(c(("10.0.0.5", 50400), ("1.1.1.1", 443)))
        check("the canary is logged apart, not counted external",
              w.flows["canary"] == 1 and w.flows["external"] == 1)

        w.reset()
        check("a new window starts from zero", w.samples == 0 and w.flows["external"] == 0)
        check("the snapshot is serialisable for the page", bool(json.dumps(w.snapshot())))
    finally:
        egress.psutil.net_connections, egress._family = real_table, real_family


async def test_execution_check() -> None:
    """The orchestrator's own check on generated code, from real sandbox runs."""
    print("\n4CE Orchestrator: execution check")
    spec = importlib.util.spec_from_file_location(
        "orchestrator", str(Path(__file__).parent / "functions" / "orchestrator.py")
    )
    orchestrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orchestrator)
    judge = orchestrator._execution_check
    sandbox = load("sandbox")

    code = "def double(x):\n    return 2 * x\nassert double(4) == 8\nprint(double(4))"
    ran = judge(code, await sandbox.run_python(code))
    check("a clean run with its assertions holding passes", ran["kind"] == "ok" and "1 assertion" in ran["text"])

    code = "assert 2 + 2 == 5, 'arithmetic'"
    ran = judge(code, await sandbox.run_python(code))
    check("a failed assertion fails, with its message", ran["kind"] == "problem" and "arithmetic" in ran["text"])

    code = "print(undefined_name)"
    ran = judge(code, await sandbox.run_python(code))
    check("a crash fails, naming the error", ran["kind"] == "problem" and "NameError" in ran["text"])

    ran = judge("print(1)", "The sovereign sandbox is unavailable, so this code was NOT executed.\n\n"
                            "Reason: the Docker daemon is not running\n")
    check("unexecuted code is unverified, and final", ran["kind"] == "unverified" and ran.get("final"))
    check("no code block is a problem", judge("", "")["kind"] == "problem")

    code = "def median(xs):\n    return sorted(xs)[len(xs) // 2]\nmedian([5, 3, 9, 1, 7])"
    ran = judge(code, await sandbox.run_python(code), "Write a function and print it for [5, 3, 9, 1, 7].")
    check("asked to print, printed nothing, is a problem", ran["kind"] == "problem" and "printed nothing" in ran["text"])

    code = "print(sorted([5, 3, 9, 1, 7])[2])"
    ran = judge(code, await sandbox.run_python(code), "Print the median of [5, 3, 9, 1, 7].")
    check("a clean run that asserts nothing is not a pass", ran["kind"] == "unverified")


async def test_figure_check() -> None:
    """The orchestrator's own check that cited figures are in what they cite."""
    print("\n4CE Orchestrator: figure check")
    spec = importlib.util.spec_from_file_location(
        "orchestrator", str(Path(__file__).parent / "functions" / "orchestrator.py")
    )
    orchestrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orchestrator)
    judge = orchestrator._figure_checks
    sources = [{"name": "SOP-MEC-014_seal_leakage.txt", "passages": [{"text":
        "2.2 Leakage between 5 and 20 drops per minute: replace within 30 days."}]}]

    kinds = lambda checks: sorted((c["kind"], c["text"].split(" ")[0]) for c in checks)
    checks = judge("Replace within 30 days [1].", sources)
    check("a figure the source holds passes", kinds(checks) == [("ok", "Every")])
    checks = judge("Replace within 14 days [1].", sources)
    check("a figure the source lacks fails", ("problem", "14") in kinds(checks))
    checks = judge("The seal leaks 18 drops per minute [1].", sources, "it leaks 18 drops/min")
    check("the request's own figure is shown, not failed",
          ("unverified", "18") in kinds(checks) and not any(k == "problem" for k, _ in kinds(checks)))
    checks = judge("Clause 5.1 forbids starting without the guard [1].", sources, "", {"5.1"})
    check("a clause the rule pack cited is not a fabrication", not any(c["kind"] == "problem" for c in checks))
    checks = judge("Clause 9.4 forbids it [1].", sources, "", {"5.1"})
    check("a clause nobody cited still fails", any("Clause 9.4" in c["text"] for c in checks))

    sop = ("## SOP assessment - SOP-MEC-014 - ATTENTION REQUIRED\n### Required actions\n"
           "- **§4.2** - Remaining wall thickness margin is below 2.0 mm. Shorten the inspection interval to six months.")
    years, basis = orchestrator._sop_interval(sop)
    check("reads the interval an SOP requires", abs(years - 0.5) < 1e-9 and basis == "the interval SOP-MEC-014 §4.2 requires")
    check("no required interval, none read",
          orchestrator._sop_interval("## SOP assessment - X\n- **§2.2** - Replace the seal.") == (0.0, ""))


async def test_calculations() -> None:
    """Remaining life by the thickness method, worked in code."""
    print("\n4CE Engineering Calculations")
    tool = load("calculations")

    out = await tool.calculate_remaining_life(
        "previous thickness 12.0 mm three years ago, current thickness 11.2 mm, required thickness 9.5 mm"
    )
    check("reproduces the worked example: 0.267 mm/year, 6.4 years, 3.2 years",
          "**0.267 mm/year**" in out and "**6.4 years**" in out and "**3.2 years**" in out)
    check("shows every step with its units", "(12.0 mm - 11.2 mm) ÷ 3 years" in out and "Step 3" in out)

    out = await tool.calculate_remaining_life(
        "readings 3 years apart\n\n| TML | Previous (mm) | Current (mm) | Required (mm) |\n|---|---|---|---|\n"
        "| TML-1 | 12.0 | 11.2 | 9.5 |\n| TML-3 | 10.4 | 9.4 | 9.5 |"
    )
    check("a survey table is worked row by row", "| TML-1 |" in out and "| TML-3 |" in out)
    check("at or below required thickness governs, and says so",
          "Governing location: TML-3" in out and "AT OR BELOW REQUIRED THICKNESS" in out)

    out = await tool.calculate_remaining_life(
        "previous thickness 12.0 mm 3 years ago, current thickness 11.2 mm, required thickness 9.5 mm, "
        "maximum interval 2 years"
    )
    check("the code maximum caps the next measurement",
          "The lesser of RL ÷ 2 (3.2 years) and the code maximum (2.0 years) = **2.0 years**" in out)

    out = await tool.calculate_remaining_life(
        "previous thickness 12.0 mm 3 years ago, current thickness 11.2 mm, required thickness 9.5 mm",
        max_interval_years=0.5, interval_basis="the interval SOP-MEC-014 §4.2 requires",
    )
    check("an SOP's shorter interval governs, and is named",
          "the interval SOP-MEC-014 §4.2 requires (6 months) = **6 months**" in out
          and "again within 6 months" in out)

    out = await tool.calculate_remaining_life("the pump leaks 18 drops/min")
    check("says what it needs when readings are missing", out.startswith("Remaining life could not be calculated"))

    import io
    from openpyxl import load_workbook
    spec = importlib.util.spec_from_file_location("deliverables_module", TOOLS / "deliverables.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    book = load_workbook(io.BytesIO(module._build_xlsx(
        "T", "x", [], [], [{"kind": "remaining_life", "max_interval": None, "rows": [
            {"location": "TML-1", "previous": 12.0, "current": 11.2, "required": 9.5, "years": 3.0}]}]
    )))
    sheet = book["Remaining life"]
    check("the workbook carries it as live formulas",
          str(sheet["G2"].value).startswith("=") and str(sheet["H2"].value).startswith("=IF("))


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

    out = await tool.check_sop_thresholds("seal leak 18 drops/min, vibration 7.1 mm/s, bearing temperature 71 C")
    check("a velocity is named, not called missing", "7.1 mm/s was given" in out and "state the zone" in out)
    check("18 drops/min needs the supervisor under §2.2", "| 18 drops/min |" in out and "§2.2 | REVIEW" in out)

    out = await tool.check_sop_thresholds(
        "previous thickness 12.0 mm three years ago, current thickness 11.2 mm, required thickness 9.5 mm"
    )
    check("current and required thickness are read as §4.1's measured and retirement",
          "§4.1 | PASS" in out and "11.2" in out)
    check("a 1.7 mm margin brings §4.2's six-month interval", "§4.2" in out and "six months" in out)


async def main() -> None:
    if not Path("data").exists():
        print("Run this from the backend/ directory so open_webui and its database resolve.")
        sys.exit(2)

    await test_sandbox()
    await test_deliverables()
    await test_sovereignty()
    await test_egress()
    await test_execution_check()
    await test_figure_check()
    await test_calculations()
    await test_sop_check()

    failed = [label for label, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("Failed: " + "; ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
