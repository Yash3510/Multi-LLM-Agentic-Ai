"""
Measure how well the vision model reads the two demo images the answer keys
describe - a handwritten shift log and a P&ID excerpt - at the sizes 4CE could
send them.

    cd backend && ../.venv/bin/python ../4ce/eval_vision.py          # macOS, Linux
    cd backend && ../.venv/Scripts/python.exe ../4ce/eval_vision.py  # Windows

Runs the orchestrator's own reading pass - its prompt, its resize, its parsing
and its ISA typing - against the model server directly, and scores what comes
back against 4ce/demo/samples/*_answer_key.txt: every reading of the log, the
smudged leakage figure flagged rather than stated, and every tag of the P&ID.

Re-run it after changing the vision model, its context, the reading prompts or
the vision_*_edge valves. Exits non-zero when the size the orchestrator
actually uses for a page misses anything.
"""

import argparse
import base64
import importlib.util
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, os.getcwd())

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "demo" / "samples"

# (words one of which the item must contain, the value it must hold)
LOG_READINGS = [
    (("seal", "leak", "weep"), "6"),
    (("press",), "18.6"),
    (("vib",), "3.9"),
    (("temp",), "74"),
    (("guard", "bolt"), "missing"),
]
PID_TAGS = {
    "T-101": "equipment", "P-101A": "equipment", "P-101B": "equipment", "E-101": "equipment",
    "HV-101A": "valve", "HV-101B": "valve", "NRV-101A": "valve", "NRV-101B": "valve", "FV-101": "valve",
    "PT-101": "instrument", "FE-101": "instrument", "FT-101": "instrument", "FIC-101": "instrument",
    '8"-P-1001-A1A': "line", '6"-P-1002-A1A': "line",
}


def orchestrator():
    spec = importlib.util.spec_from_file_location("orchestrator", str(HERE / "functions" / "orchestrator.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vision_model() -> str:
    registry = json.loads((HERE / "models.json").read_text(encoding="utf-8"))
    return next(m["id"] for m in registry["models"] if "vision" in m.get("capabilities", []))


def read(o, base: str, model: str, path: Path, kind: str, edge: int) -> tuple[list[dict], float]:
    part = {"type": "image_url", "image_url": {
        "url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()}}
    image = o._decode_image(part)
    body = {
        "model": model,
        "max_tokens": o.Pipe().valves.extraction_max_tokens,
        "messages": [
            {"role": "system", "content": o._READER_SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": o._READ_PROMPTS[kind] + "\n\n/no_think"},
                o._shrink_image(part, edge) if edge else part,
            ]},
        ],
    }
    request = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    started = time.monotonic()
    reply = json.loads(urllib.request.urlopen(request, timeout=900).read())["choices"][0]["message"]["content"]
    return o._parse_fields(reply, kind, o._sent_size(image.size, edge)), time.monotonic() - started


def score_log(fields: list[dict]) -> tuple[int, bool]:
    found, flagged = 0, False
    for words, value in LOG_READINGS:
        match = next((f for f in fields if any(w in f["item"].lower() for w in words)
                      and value in f["value"].lower()), None)
        if match:
            found += 1
            if value == "6":
                flagged = match["check"]
    return found, flagged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:1234/v1", help="the model server's OpenAI-compatible URL")
    parser.add_argument("--model", default="", help="defaults to the first vision model in models.json")
    parser.add_argument("--edges", default="900,1400,2200", help="longest edges to try, comma-separated")
    parser.add_argument("--runs", type=int, default=1, help="reads per image and size; the model varies run to run")
    args = parser.parse_args()

    o = orchestrator()
    model = args.model or vision_model()
    edges = [int(e) for e in args.edges.split(",") if e.strip()]
    used = o.Pipe().valves.vision_page_edge
    if used not in edges:
        edges.append(used)
    print(f"Reading pass on {model}; 4CE sends a page or a drawing at up to {used} px.\n")

    missed = False
    totals: dict = {}
    for run in range(1, args.runs + 1):
        if args.runs > 1:
            print(f"Run {run} of {args.runs}")
        for edge in edges:
            fields, seconds = read(o, args.base, model, SAMPLES / "shift_log_P-101.png", "page", edge)
            found, flagged = score_log(fields)
            print(f"  handwritten log  @ {edge:>4} px: {found}/{len(LOG_READINGS)} readings, "
                  f"smudged figure {'flagged' if flagged else 'NOT flagged'}, {seconds:.0f}s")
            if edge == used and (found < len(LOG_READINGS) or not flagged):
                missed = True
            log = totals.setdefault(("log", edge), [0, 0, 0.0])
            log[0] += found == len(LOG_READINGS)
            log[1] += flagged
            log[2] += seconds

            fields, seconds = read(o, args.base, model, SAMPLES / "pid_P-101_excerpt.png", "drawing", edge)
            tags = {f["tag"]: f["type"] for f in fields}
            right = [t for t, kind in PID_TAGS.items() if tags.get(t) == kind]
            extra = sorted(set(tags) - set(PID_TAGS))
            print(f"  P&ID excerpt     @ {edge:>4} px: {len(right)}/{len(PID_TAGS)} tags read and typed"
                  + (f"; missing {sorted(set(PID_TAGS) - set(right))}" if len(right) < len(PID_TAGS) else "")
                  + (f"; also listed {extra}" if extra else "") + f", {seconds:.0f}s")
            if edge == used and len(right) < len(PID_TAGS):
                missed = True
            pid = totals.setdefault(("pid", edge), [0, 0, 0.0])
            pid[0] += len(right)
            pid[2] += seconds

    if args.runs > 1:
        n = args.runs
        print(f"\nOver {n} runs:")
        for edge in edges:
            log, pid = totals[("log", edge)], totals[("pid", edge)]
            print(f"  @ {edge:>4} px: log complete in {log[0]}/{n}, smudge flagged in {log[1]}/{n}, "
                  f"~{log[2] / n:.0f}s; P&ID {pid[0] / n:.1f}/{len(PID_TAGS)} tags on average, ~{pid[2] / n:.0f}s")

    print("\nThe model reads differently run to run; measure more than once before changing a valve.")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
