---
title: Testing
type: testing
status: active
updated: 2026-09-25
tags:
  - 4ce
  - testing
---

# Testing

What checks 4CE, how to run each check, and what each one does not cover. The
headline verification table, with the evidence behind each row, is in the
[project README](../../README.md#verification-status). This page is about the
instruments that produce that evidence.

---

## At a glance

| Instrument | Checks | Needs | Run from |
|---|---|---|---|
| [`test_tools.py`](../test_tools.py) | Every tool and the orchestrator's deterministic logic, success and failure paths | Backend database; Docker for the sandbox suite | `backend/` |
| [`preflight.py`](../preflight.py) | That this machine is in the state a demo depends on | Model server, Docker, running backend | repository root |
| [`eval_retrieval.py`](../eval_retrieval.py) | That retrieval finds the right clause and the relevance guard keeps it | Running backend with the Plant SOPs knowledge base | `backend/` |
| [`eval_vision.py`](../eval_vision.py) | How well the reading pass reads the two demo images, at each size | Model server with the vision model loaded | `backend/` |

`python` below means the repository's virtual environment:
`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on macOS and Linux.

---

## Tool suite - `test_tools.py`

```bash
cd backend && ../.venv/Scripts/python.exe ../4ce/test_tools.py
```

Each tool is loaded from source the way the application loads it, then driven
through its success and failure paths. The last line is `N/M checks passed`,
and the script exits non-zero on any failure, so it can gate a demo-day check.
The current total is recorded in [SETUP_MACOS.md](SETUP_MACOS.md#12-confirm-it-actually-works).

| Suite | What it asserts |
|---|---|
| `test_sandbox` | Code executes and returns stdout; outbound network is blocked; the workspace is read-only; the wall-clock limit is enforced; files written to `/output` are returned, and oversized ones are refused; failures are reported honestly |
| `test_deliverables` | Valid OOXML with the content and classification banner; empty or unattributed requests are refused; an image the answer shows is embedded in the Word report and given a slide in the deck |
| `test_sovereignty` | Produces the audit table and a verdict, states its own limits and whether egress was observed; loopback and private addresses classify as on-premise, public hosts as external |
| `test_egress` | A flow is counted once across samples; the model server is in scope by its port; LAN clients and the configured LAN endpoint are not leaks, other outbound flows are flagged with the process that made them; the canary is logged apart; a browser the model server opened is not counted as the model server; a new window starts from zero |
| `test_audit_trail` | Each entry follows the one before, from the genesis hash; entries carry their run; an untouched trail verifies; a reopened trail continues the same chain; an entry changed after writing, or removed, breaks the chain at that entry; a trail that cannot be written says so and does not raise; offline mode refuses a guarded library's download when its module is first imported, including the document loader's spaCy download |
| `test_workspace_tools` | Writes stay inside the workspace and keep the earlier version; `..`, absolute paths, executable types and the kept versions are refused; a workbook is read with its cell letters and formulas; a survey's formulas use its own columns and go to a copy while the source is untouched; the copy's formulas give what the calculation gives; each survey location gets the interval the rule pack gives it; a preview writes nothing; a formula reaching outside the workbook and overwriting the source are refused; a CSV becomes a workbook copy; an answer claiming the workbook already has the results, or that a clause the rule pack applied does not apply, is a problem |
| `test_execution_check` | 4CE's own verdict on a sandbox report: crash, timeout, missing code block, printed nothing, asserted or not |
| `test_figure_check` | A figure cited to a source that does not contain it fails; a requester's own figure, or a clause the rule pack cited, does not; an invented SOP limit fails; a clock time is not a figure; a figure another source holds, or the rule pack gives, is shown as mis-cited rather than invented; two documents sharing a code are named apart; an answer calling a REVIEW reading within limits fails; the relevance guard keeps only passages that share words with the request or match strongly |
| `test_calculations` | Corrosion rate, remaining life and next inspection against the worked example (0.267 mm/year, 6.4 years), including the SOP-required interval cap |
| `test_routing` | Task types route by registry capability; a new registry entry appears with no code change; a valve override still wins and says so; the orchestrator's built-in registry matches [`models.json`](../models.json); every hardware profile has a model for every task type, sets only real valves, and routes as planned; only the laptop profile claims a measurement |
| `test_vision` | Image kind decides the size (P&ID and shift log as pages, anything else a photo); fields kept from a reply cut off mid-object, numbered, with units and pixel boxes; low confidence marked for checking; ISA tag typing (`PT 101` is `PT-101`, `FE` is an instrument); labels and title blocks are not tags; page readings reach the rule pack; the annotated copy is a PNG of the image's size |
| `test_sop_check` | Band boundaries, the worse end of a range, `NO DATA` for a missing reading, unassessed readings listed, malformed rule packs rejected; a missing guard "bolt" fails §5.1 and a defect reported absent ("no visible spray") passes |

**Does not cover:** model output. Nothing here calls a language model, so the
suite says nothing about answer quality. The evals and the demo prompts cover
that.

---

## Preflight - `preflight.py`

```bash
python 4ce/preflight.py          # report
python 4ce/preflight.py --fix    # also load the models at the context 4CE needs
python 4ce/preflight.py --base http://127.0.0.1:8081
```

Fifteen checks, each added because it once failed and cost real time to
diagnose:

| Check | Fails when |
|---|---|
| Each registry model (two) and the embedding model | Not installed, not loaded, or loaded above its registry context |
| Docker | Not on PATH, or the daemon is not responding |
| Sandbox image | `python:3.12-alpine` not pulled |
| Backend | `/health` unreachable |
| Admin sign-in | The demo account is rejected |
| Tools installed | Any of the seven `ace_*` tools is missing |
| Orchestrator model | The pipe is not served |
| Tools attached | The tools are not on the orchestrator's model record |
| Approval gate | `require_approval` is off (a warning) |
| Speech to text | Whisper weights not cached, or a non-local engine (a warning) |
| Knowledge attached | No intact knowledge base on the orchestrator |
| Egress watch | Not running, or something has left the machine (a warning, naming the process and address) |
| Audit trail | Not served, broken at an entry, or entries that could not be written (a warning) |

A sixteenth line, **Egress rule**, appears as a warning when the canary
reached the internet, meaning nothing on the host blocks egress.

**Does not cover:** whether the models answer well, or how fast.

---

## Retrieval evaluation - `eval_retrieval.py`

```bash
cd backend && ../.venv/Scripts/python.exe ../4ce/eval_retrieval.py
```

| | |
|---|---|
| **Objective** | Retrieval returns the clause each answer must come from, and the relevance guard keeps it while emptying questions the documents cannot answer |
| **Procedure** | 15 questions about SOP-MEC-014 and the P-101B readings, each with the clause text its answer needs; 3 unrelated questions. Top 4 retrieved, then the orchestrator's `_relevant` guard applied |
| **Result** (commit `2b0d6c9`, 2026-09-24) | 15/15 found in the top 4, 13 at rank 1; the guard kept 15/15; 3/3 unrelated questions emptied |
| **Re-run after** | Changing the embedding model, chunking, `retrieval_k` or the guard |
| **Limitations** | One knowledge base of two documents. It measures finding the passage, not the answer written from it |

---

## Vision evaluation - `eval_vision.py`

```bash
cd backend && ../.venv/Scripts/python.exe ../4ce/eval_vision.py --runs 3
```

| | |
|---|---|
| **Objective** | The reading pass reads every figure of a handwritten log, flags its smudged figure rather than stating it, and reads every tag of a P&ID |
| **Procedure** | The orchestrator's own reading pass (prompt, resize, parsing, ISA typing) against the model server, scored against [`shift_log_P-101_answer_key.txt`](../demo/samples/shift_log_P-101_answer_key.txt) and [`pid_P-101_excerpt_answer_key.txt`](../demo/samples/pid_P-101_excerpt_answer_key.txt) |
| **Result** (commit `195cb9f`, qwen3-vl-4b at 8192, three runs per size) | 900 px: log complete 0/3, smudge flagged 0/3, P&ID 14.7 of 15 tags. 1400 px: 3/3, 2/3, 15.0. 2200 px: 3/3, 3/3, 15.0. About 11 s per log read |
| **Re-run after** | Changing the vision model, its context, the reading prompts or the `vision_*_edge` valves |
| **Limitations** | Two images. The flag rests on the model's own confidence, which varies run to run. The boxes are approximate: on the P&ID one or two sit a label away |

Full table with timings: [HOW_TO_RUN.md - Reading images](HOW_TO_RUN.md#reading-images).

---

## Verified by hand

Recorded in the commit that made each change, with the evidence there.

| What | Result | Commit |
|---|---|---|
| Approval gate, empty box | Withheld, recorded as rejected | `aca731e` |
| Sign-off survives a page reload | Panel back in under 5 s; release completed | `080bb60` |
| Knowledge base recovery after *Reset vector DB* | Rebuilt by one `install.py` run; retrieval identical (3,244 characters, clauses 2.1 and 2.2) | `4b8aa91` |
| Microphone with `HF_HUB_OFFLINE` set | Transcribes from cached Whisper weights with no network | `12d2d87` |
| Sandbox on Windows after the macOS environment fix | Docker reachable both ways; tool suite 44/44 at the time | `52b927e` |
| Egress watch on first run | Caught the model server contacting a Cloudflare address for updates while the configuration audit read 18/18 | `91152df` |
| Production build | Completed in 2 m 8 s with a 6 GB Node heap | `1d69f02` |
| Audit trail, one approval note end to end | Eleven entries - request to release - verified; the released fingerprint equals the verified draft's hash | `a729426` |
| Survey workbook copy, opened in Excel | Excel calculates the copy's formulas to the calculation tool's values (0.267 mm/year, 6.375 years, next inspection 0.5 years at §4.2 locations) | `a729426` |
| Egress watch on the first spreadsheet upload | Caught the backend reaching GitHub: the document loader installing spaCy's `en_core_web_sm` at run time, with the configuration audit reading 18/18 | `a729426` |

---

## Known failures and limits

| Symptom | Cause | Handling |
|---|---|---|
| A code answer cut off mid-block, then an ULTRON FAIL | A model that reasons at length hits the per-agent `max_tokens` (900) | Re-run, or raise the valve and accept a slower turn |
| Prose instead of code on a harder prompt | The 1.7B model; seen on an ISO 10816 zone converter | Keep code prompts simple |
| "request exceeds the available context size" | A pasted document longer than the 8192-token context | Attach the file instead, so retrieval sends only relevant passages |
| ULTRON's line-by-line checks disagree with its verdict | Small-model verifier | The verdict word decides; objections under a PASS are shown as reservations |
| Egress between two samples, or DNS lookups, not counted | The watch samples sockets every 250 ms | Stated on the Sovereignty page; a capture on the uplink closes the gap |

---

## Related documentation

- [AGENT_CHAIN.md](AGENT_CHAIN.md) - the stages these checks cover
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md) - end-to-end prompts with measured timings
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - the setup the checks assume
