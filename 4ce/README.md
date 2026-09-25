# 4CE plugin sources

Our sovereign agentic layer, kept as source here and loaded into the running app at
runtime. Everything under `4ce/` is ours; nothing upstream is modified, so the fork
stays mergeable.

See [`docs/deep-research.md`](docs/deep-research.md) for the full porting analysis this
was built from, and [`Multi-LLM-Docs`](https://github.com/Yash3510/Multi-LLM-Agentic-Ai/blob/main/README.md) for the original
STARK architecture spec and standalone prototype these plugins port over from.

## functions/orchestrator.py — the 4CE Orchestrator

A **pipe function**: it registers itself as a selectable model and owns the whole turn.

### Install

1. Start 4CE and sign in as admin.
2. Go to **Admin → Functions → +** (`/admin/functions/create`).
3. Paste the contents of `functions/orchestrator.py`, save, and toggle it **on**.
4. It now appears in the model picker as **4CE / TONY (Orchestrator)**.

No rebuild is needed — functions live in the database and are loaded per call.

### Configure

Open the function's **Valves** and set the model names to whatever your local server
actually serves (check **Admin → Settings → Connections**, or the model dropdown):

**Routing** — which model each *task type* goes to. This is what drives automatic
model selection:

| Valve | Purpose |
|---|---|
| `analysis_model` | General reasoning and document work |
| `coding_model` | Code generation and debugging |
| `vision_model` | Scanned documents, drawings, photographs |

**Agent assignment** — pin an individual agent to its own model. Blank means the
agent follows whatever the router chose, so routing stays the default behaviour:

| Valve | Purpose |
|---|---|
| `friday_model` | Grounding and analysis |
| `jarvis_model` | Producing the deliverable |
| `ultron_model` | Verification. Setting this to a *different* model from JARVIS is worth doing: otherwise a model is grading its own work. |

**Behaviour and performance:**

| Valve | Purpose |
|---|---|
| `vision_max_edge` | Longest edge a photograph is downscaled to before it reaches the vision model (default 900). A full-page 200 dpi scan costs minutes on a 6 GB GPU; downscaling is the single biggest win. 0 sends it untouched. |
| `vision_page_edge` | Longest edge for a page or a drawing - a scan, a handwritten log, a P&ID (default 2200). Handwriting needs the pixels: over three runs the demo shift log lost a reading every time at 900 px and its smudge was never flagged; at 2200 px every reading came back and the smudge was flagged each time. `eval_vision.py` measures it. |
| `vision_extraction` | Read an image once into numbered fields - tag, value, unit, confidence - each boxed where it was read, before FRIDAY analyses it (default on). The boxed copy and the table go into the draft, the answer and the Word report. |
| `extraction_max_tokens` | Reply budget for that reading pass (default 2400). A P&ID's tag list runs to about 1,600 tokens. |
| `max_tokens` | Upper bound per agent reply (default 900). A reasoning model left unbounded will happily run for minutes. |
| `chat_model` | Small, fast model for greetings and questions about the assistant |
| `orchestrate_small_talk` | Send greetings through the full chain too. Off by default. |
| `enable_verification` | Run the ULTRON pass |
| `enable_replan` | Allow one TONY replan when ULTRON fails. Roughly doubles worst-case turn time. |
| `require_approval` | Require a human to type APPROVE before release |
| `show_trace` / `show_reasoning` / `show_model_thinking` | How much provenance to append to the answer |

### The approval gate fails closed

Approval asks the reviewer to **type APPROVE**. An empty box, a different word, a
cancel or a timeout all withhold the deliverable. This is deliberate: the confirm
dialog treats a stray Enter as a "yes" unless focus happens to sit on a button, so
a yes/no prompt could release unreviewed work by reflex.

Model names are matched loosely — `qwen3-vl-4b` will resolve against something like
`qwen/qwen3-vl-4b@q4_k_m`. If a configured model isn't served, the router falls back to
an available one and says so in the trace rather than failing silently.

### What it does per turn

```
TONY      classify task (chat | code | vision | document | analysis) + report the signals
          - a purely conversational message answers directly here and stops
ROUTER    pick the local model for that task type + report why
FRIDAY    ground and analyse (RAG context arrives already injected if a
          knowledge collection is attached to the model)
JARVIS    produce the deliverable
ULTRON    challenge it -> PASS / FAIL
TONY      replan once on FAIL, re-running FRIDAY and JARVIS with the challenge
HUMAN     approve or reject before release
```

Progress is emitted as live status events, so the agent chain is visible in the UI as it
runs — driven by real execution, never simulated.

### Reasoning is visible, not hidden

Every answer carries an **Agent reasoning** section with one expandable block per step:

- **TONY** — the task type, the signals that matched, the model chosen, why, and the full
  candidate routing table. This is the model-auto-selection criterion, shown rather than claimed.
- **FRIDAY / JARVIS / ULTRON** — each agent's full output, with the model used and how long
  it took.
- **Model's internal reasoning** — a nested block holding the model's own `<think>` content.
  Reasoning models such as qwen3 emit it, and it is stripped out of the deliverable and shown
  here instead, so raw tags never leak into an approval note.

`show_reasoning` and `show_model_thinking` valves turn these off if a cleaner answer is wanted.

### Mapping to the SIH criteria

| Criterion (PS 26117) | Where it shows |
|---|---|
| Model auto-selection across ≥2 task types | TONY + ROUTER lines, visible per turn |
| Agentic task end to end | FRIDAY → JARVIS → ULTRON → approval |
| Verification and replanning | ULTRON verdict + one TONY replan |
| Human in the loop | Approval dialog; rejection withholds the deliverable |
| Multimodal | Image parts are detected and routed to the vision model |
| Auditability | Execution trace appended to every answer |

## tools/ — capabilities the agents call

Install each the same way, under **Workspace → Tools → +**, then enable them on the
4CE model so JARVIS can call them.

| Tool | What it does |
|---|---|
| `tools/sandbox.py` | Runs generated Python in a disposable container: no network, read-only root, all capabilities dropped, no privilege escalation, hard CPU/memory/PID/time caps. Says so plainly when Docker is unreachable instead of pretending the code ran. |
| `tools/deliverables.py` | Renders the released answer as real office files, stored locally with a download link: a formatted `.docx` (classification banner, reference table, headings and bullets), an `.xlsx` with one sheet per table - numbers as numbers, units in headers, a stated total as a live `SUM` once it is checked to add up - and a `.pptx` deck with a slide per section, native table slides and speaker notes. Workbooks and decks also carry the SOP rule pack's verdict table verbatim, and every file carries the approval record. |
| `tools/sovereignty.py` | Audits live configuration for anything that could carry data off-premise and returns a pass/fail table. |
| `tools/sop_check.py` | Assesses inspection readings against the thresholds in an SOP and returns a clause-cited fit-for-service verdict. The comparisons are arithmetic done locally against an authored rule pack, so the accept/reject decision never rests on a model's judgement. See [`docs/SOP_THRESHOLD_PLAN.md`](docs/SOP_THRESHOLD_PLAN.md). |
| `tools/calculations.py` | Works engineering calculations in code with every step shown and units carried: corrosion rate, remaining life and the next thickness measurement, from a sentence or a thickness-survey table. An inspection interval the SOP rule pack requires caps the next measurement - for a survey, location by location - and a workbook carries the calculation as live formulas. |
| `tools/files.py` | Reads, lists and writes text files in one workspace folder (`DATA_DIR/4ce/workspace` by default), plus any read-only folders it is given, such as an SOP share. A path that would leave the workspace - `..`, an absolute path, a drive letter, a link out - is refused; so is any type but text. Overwriting a file keeps the earlier version under `.versions/`, and every read and write is recorded in the audit trail with the file's SHA-256. |
| `tools/sheets.py` | Reads an Excel workbook or a CSV - attached to the chat or in the workspace - as tables with every cell's reference and formula, and writes changes to a copy, never the source, as live formulas. A formula that could reach outside the workbook (`WEBSERVICE`, an external link, DDE, `HYPERLINK`) is refused. A small evaluator - arithmetic, comparisons, `IF`, `MIN`, `MAX`, `SUM` and a few more, walked node by node rather than handed to `eval` - reports what the new cells will show, so the copy's numbers can be checked against 4CE's own calculation. |

### Sandbox deployment note

The sandbox shells out to `docker`. If the 4CE backend itself runs inside a container it
cannot spawn sibling containers unless the Docker socket is mounted, which hands that
container full control of the host daemon. **For the demo, run the backend natively on the
host** and let it drive Docker Desktop — simpler and safer. The tool reports the problem
clearly rather than failing silently either way.

Pre-pull the sandbox image (`docker pull python:3.12-alpine`) **before** going offline, or
the first execution will fail with nothing to run.

Also disable the built-in interpreter (`ENABLE_CODE_INTERPRETER=false`,
`ENABLE_CODE_EXECUTION=false`) so there is exactly one execution path to explain: the
browser-side Pyodide default is weaker than this sandbox and muddies the story.

## The audit trail

Every request leaves an append-only, hash-chained record in `DATA_DIR/4ce/audit.jsonl`
(`backend/open_webui/utils/fource_audit.py`): the request, the documents retrieved, the
model it was routed to, every model call and tool call with the SHA-256 of what went in
and what came out, every file read or written, ULTRON's verdict, who approved, and the
fingerprint of what was released - which is the same SHA-256 the receipt, the provenance
and the Word report print. Entries hold names, counts and hashes, never the text itself.

Each entry carries the hash of the one before it, so an entry changed or removed breaks
the chain from that point and a verification names it. The Sovereignty page shows the
trail live, with a button that walks and checks the whole chain; every answer's provenance
names the entries its run wrote and the chain's head at that moment; preflight fails a
trail that no longer verifies. It is tamper-evident rather than tamper-proof - anyone who
can write the file can rewrite the whole chain after it - so keep a copy of the head hash
somewhere they cannot reach.

## Verification status

Verified against a running instance with Bionic serving `qwen3-vl-4b`,
`qwen3-1.7b` and `text-embedding-nomic-embed-text-v1.5`:

| Capability | Status |
|---|---|
| Model auto-selection across task types | Verified — a coding request routes to `qwen3-1.7b`, a document request to `qwen3-vl-4b`, each with the rationale shown |
| Per-agent model assignment | Verified — ULTRON runs on a different model from JARVIS |
| Agentic chain end to end | Verified — FRIDAY → JARVIS → ULTRON with a TONY replan on failure |
| Verification catches errors | Verified — ULTRON rejected fabricated inspection readings and forced a replan |
| Human approval | Verified in the browser — approve releases, reject and empty-box both withhold |
| Sandboxed code execution | Verified — 6/6 checks including blocked network, read-only workspace, enforced timeout |
| Word deliverables | Verified — 7/7 checks, valid OOXML with content and classification banner |
| Sovereignty audit | Verified — 19/19 surfaces pass on the demo configuration |
| Local RAG | Verified — upload, embed, index and query in ~0.3 s, and a grounded answer citing SOP thresholds |
| Multimodal / vision | Verified — a scanned report, a handwritten log and a P&ID read into boxed fields; `eval_vision.py` measures it |
| Workspace files and spreadsheets | Verified — writes versioned and confined to the workspace; a thickness survey's copy gets live formulas whose values match 4CE's calculation |
| Audit trail | Verified — every model call, tool call, file write, approval and release of a run recorded and the chain verified; a changed or removed entry is caught |

### The vision path and the model server's context

On a 6 GB GPU the vision model is loaded with a 65k context window, so weights plus
KV cache exceed VRAM and inference silently falls back to CPU: the server reports
`GENERATING` at ~2% GPU utilisation and a single turn runs past twenty minutes.

The same model answers the same document correctly in **19 seconds** at 760 px with a
200-token cap, so this is a configuration problem, not a capability one. The
`vision_max_edge` and `max_tokens` valves bound what this plugin controls. The rest is
on the model server: **reload the vision model with a context length of around 8192**,
which is ample for a page of text and leaves the KV cache inside VRAM.

With the vision model reloaded at 8192, the demo images read in 10-35 seconds each; see
"Reading images" in `docs/HOW_TO_RUN.md` for the measurements.

### Still open

Nothing from the original list. The SIH26117 briefing's remaining items are tracked as they are built.
