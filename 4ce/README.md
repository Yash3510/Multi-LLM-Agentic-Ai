# 4CE plugin sources

Our sovereign agentic layer, kept as source here and loaded into the running app at
runtime. Everything under `4ce/` is ours; nothing upstream is modified, so the fork
stays mergeable.

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

| Valve | Purpose |
|---|---|
| `analysis_model` | General reasoning and document work |
| `coding_model` | Code generation and debugging |
| `vision_model` | Scanned documents, drawings, photographs |
| `verifier_model` | ULTRON's challenge pass (blank = reuse the routed model) |
| `enable_verification` | Run the ULTRON pass |
| `enable_replan` | Allow one TONY replan when ULTRON fails |
| `require_approval` | Human approval dialog before release |
| `show_trace` | Append the execution trace to the answer |

Model names are matched loosely — `qwen3-vl-4b` will resolve against something like
`qwen/qwen3-vl-4b@q4_k_m`. If a configured model isn't served, the router falls back to
an available one and says so in the trace rather than failing silently.

### What it does per turn

```
TONY      classify task (code | vision | document | analysis) + report the signals
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
| `tools/deliverables.py` | Renders agent output into a formatted `.docx` — classification banner, reference table, headings and bullets — stores it locally and returns a download link. |
| `tools/sovereignty.py` | Audits live configuration for anything that could carry data off-premise and returns a pass/fail table. |

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

### Still open

- Wiring the sandbox result back through ULTRON so verification covers *executed* output.
- A dedicated security page in the UI; the sovereignty tool currently reports into chat.
- Porting the citation-discipline guard from `sovereign_ai/knowledge.py`.
