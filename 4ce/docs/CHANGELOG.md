---
title: Changelog
type: changelog
status: active
updated: 2026-09-25
tags:
  - 4ce
  - git-history
---

# Changelog

Notable changes to 4CE, newest first. Trivial formatting changes are left out.
Each entry names its commit. The detail behind each date is in the
[development timeline](history/README.md).

The root `CHANGELOG.md` belongs to the upstream platform, not to 4CE.

---

## 2026-09-25

### Added

- Hardware profiles for 24, 48 and 80 GB machines beside the measured laptop
  one, installed with `install.py --profile` and checked by `preflight.py
  --profile`; each sets the orchestrator valves that suit its GPU, and the
  Sovereignty page names the one installed.
- An append-only, hash-chained audit trail: each run's request, sources,
  route, model and tool calls with input and output hashes, file writes,
  verdict, approval and release. Shown live and verified on the Sovereignty
  page, named in each answer's provenance, checked by preflight (`a729426`).
- Workspace file tools - read, list and write in one folder, earlier versions
  kept - and spreadsheet tools that read a workbook with its formulas and write
  changes to a copy as live formulas (`a729426`).
- A thickness survey attached to a request is assessed location by location
  against the SOP rule pack, and the copy's changes are previewed in the draft
  for the reviewer to approve (`a729426`).
- 4CE checks for an answer saying a workbook already holds what 4CE is about
  to add, and for one saying a clause the rule pack applied does not apply
  (`a729426`).
- A thickness survey workbook among the demo samples (`a729426`).

### Security

- The document loader installed spaCy's `en_core_web_sm` from GitHub while
  processing the first spreadsheet uploaded. Offline mode now refuses run-time
  downloads, and the configuration audit checks the model is installed
  (`a729426`).

- An image reading pass. Scans, handwriting and drawings are read into
  numbered fields with units, confidence and pixel boxes, and drawn on a
  numbered copy for the reviewer (`195cb9f`).
- `eval_vision.py`, and two demo samples with answer keys: a handwritten shift
  log and a P&ID excerpt (`195cb9f`).
- A 4CE check that fails an answer calling a reading within limits when the
  rule pack says REVIEW or FAIL (`195cb9f`).

### Changed

- Pages and drawings are sent to the vision model at up to 2200 px (`195cb9f`).

### Fixed

- A defect reported absent ("no visible spray") no longer fails the SOP check
  (`195cb9f`).
- The dev server no longer reloads the page, dropping a sign-off in progress,
  when backend, plugin or doc files change (`195cb9f`).

## 2026-09-24

### Added

- An egress watch, the Sovereignty page, a canary and per-run external counts
  (`91152df`).
- Excel workbooks and PowerPoint decks as deliverables (`7d5e304`).
- A calculation tool for corrosion rate, remaining life and next inspection,
  with steps shown (`11f9ac1`).
- A relevance guard on retrieval, "no citation, no claim", and
  `eval_retrieval.py` (`2b0d6c9`).
- `models.json` as the routing registry (`456e7f8`).
- A trust view in answers, a route preview under the message box, and sidebar
  outcome marks (`33dac53`, `8157ad4`).

### Changed

- A sandbox failure fails the result before ULTRON is consulted, and a pass
  with objections reads "with N reservations" (`8559acc`).

### Fixed

- The next inspection interval now respects SOP-MEC-014 §4.2 (`11f9ac1`).
- Pyodide copy failures on Windows, and the production build running out of
  heap (`b898277`, `1d69f02`).
- The upstream licence text, missing since 2026-09-20, was restored unchanged
  (`ad1becd`).

## 2026-09-22 to 2026-09-23

### Added

- A stage rail, live status line, overview tree, intro animation and failure
  card (`8256bb6`, `4214451`, `d119bbb`, `b717f74`).
- Numbered sources with passage chips, a figure check, SHA-256 fingerprints,
  "What changed on try 2", and an audit sheet (`dcc2d43`, `b18f785`,
  `dca074e`).
- A sign-off panel that reviews checks and sources, and survives a tab
  reconnect (`e8c8163`, `080bb60`).
- The Word report in the 4CE house style, with a preview before download
  (`6ce13f3`, `252c301`).

### Changed

- An unanswered sign-off is recorded as *not obtained*, not as rejected
  (`6ce13f3`).
- Hold-to-release was tried and replaced by the typed `approve` again
  (`e8c8163`, `f276768`).

## 2026-09-20

### Added

- A knowledge-base check in preflight, and `install.py` rebuilds the knowledge
  base (`a3f5e3c`, `4b8aa91`).
- A macOS setup guide (`52b927e`).
- Obsidian vault settings (`553e592`).

### Changed

- The sovereignty audit grew from 11 to 18 checks (`b55ba41`).

### Removed

- "Attach Webpage", the Integrations panes (properly this time), and the
  Ollama-only parameters (`b55ba41`, `9232d5f`, `777a46b`).
- Third-party image and speech endpoints, blanked on install (`304bb75`,
  `9339c0a`).
- `LICENSE` was emptied and deleted (`badd4de`, `fb20d89`); restored on
  2026-09-24.

### Fixed

- A stopped run records what it spent and closes its status line (`1854bb0`).
- A context overflow reports the server's reason, not "empty response"
  (`cef4459`).

## 2026-09-18 to 2026-09-19

### Added

- `preflight.py` (`9ad0c59`) and the demo script (`29d7923`).
- Typed files from code blocks, and a writable `/output` in the sandbox
  (`04173c1`).

### Changed

- The chain calls its tools. ULTRON runs on a different model from JARVIS by
  default (`fef00fe`).
- The chain retrieves for itself and reports how much grounding arrived
  (`09cc868`, `e1a0682`).
- The model picker offers only the routed models (`e872139`).
- The microphone transcribes with locally cached Whisper weights. Calendar,
  automations and channels are disabled (`12d2d87`).

### Removed

- Gravatar and browser speech-to-text (`b9a1a81`).

### Fixed

- Every code block is executed, not just the first, and unfenced code is
  recovered (`327e143`, `2e254d8`).
- The provenance table reports what ran, and elapsed time excludes the
  reviewer's wait (`d7cfde5`).

## 2026-09-13 to 2026-09-16

### Added

- The SOP threshold checker (`f2c1de6`).
- SECURITY, CONTRIBUTING and CITATION files (`27b5c43`).

### Changed

- The supplied 4CE mark on every icon, and a rewritten first-run screen
  (`0bc689f`, `b440633`, `69df476`).
- Documentation moved under `4ce/docs/` (`0bc341d`).

### Fixed

- The backend no longer deletes its own static files in dev (`5e86b9e`).

## 2026-09-10 to 2026-09-11

### Added

- `HOW_TO_RUN.md` (`1751dd7`) and a 4CE README (`8e6d22e`).

### Changed

- The 4CE name carried through the interface (`64f5bf1`); the backend's icons
  branded (`83b3689`).

### Removed

- The admin Help block and the About pane (`61de603`, `339636c`).

## 2026-09-08

### Added

- The agent chain (TONY, FRIDAY, JARVIS, ULTRON, human approval), the
  sandbox, the Word deliverable, the sovereignty audit and the installer
  (`2646819` to `c256b89`).
- Agent reasoning blocks and the provenance table (`07262ed`, `d5dfbcf`).
- Per-agent model valves and the tool test suite (`285c8ce`).
- The conversational fast path (`abbcab7`).

### Changed

- Approval requires typing APPROVE (`aca731e`).
- Images and replies are bounded (`5223fdb`).
