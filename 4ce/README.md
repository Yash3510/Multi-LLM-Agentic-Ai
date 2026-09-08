# 4CE plugin sources

Our sovereign agentic layer, kept as source here and loaded into the running app at
runtime. Everything under `4ce/` is ours; nothing upstream is modified, so the fork
stays mergeable.

See [`../deep-research.md`](../deep-research.md) for the full porting analysis this
was built from, and [`Multi-LLM-Docs`](../../Multi-LLM-Docs/README.md) for the original
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
| `vision_max_edge` | Longest edge an image is downscaled to before it reaches the vision model (default 900). A full-page 200 dpi scan costs minutes on a 6 GB GPU; downscaling is the single biggest win. 0 sends the image untouched. |
| `max_tokens` | Upper bound per agent reply (default 900). A reasoning model left unbounded will happily run for minutes. |
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

## Verification status

Verified against a running instance with LM Studio serving `qwen3-vl-4b`,
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
| Sovereignty audit | Verified — 6/6 checks, 11/11 surfaces pass on the demo configuration |
| Local RAG | Verified — upload, embed, index and query in ~0.3 s, and a grounded answer citing SOP thresholds |
| **Multimodal / vision** | **Not yet verified** — see below |

### The vision path needs a model-server change

On a 6 GB GPU the vision model is loaded with a 65k context window, so weights plus
KV cache exceed VRAM and inference silently falls back to CPU: the server reports
`GENERATING` at ~2% GPU utilisation and a single turn runs past twenty minutes.

The same model answers the same document correctly in **19 seconds** at 760 px with a
200-token cap, so this is a configuration problem, not a capability one. The
`vision_max_edge` and `max_tokens` valves bound what this plugin controls. The rest is
on the model server: **reload the vision model with a context length of around 8192**,
which is ample for a page of text and leaves the KV cache inside VRAM.

Re-run the vision check after that change before relying on the multimodal demo.

### Still open

- Wiring the sandbox result back through ULTRON so verification covers *executed* output.
- A dedicated security page in the UI; the sovereignty tool currently reports into chat.
- Porting the citation-discipline guard from `sovereign_ai/knowledge.py`.
