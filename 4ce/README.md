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

### Not yet wired

- **Sandboxed code execution** — port `sovereign_ai/sandbox.py` as a Tool and have JARVIS
  call it. The built-in Pyodide interpreter is browser-side and weaker; disable it so
  there is only one execution story.
- **DOCX/XLSX deliverables** — port `sovereign_ai/deliverables.py` as a Tool.
- **Sovereignty counters** — a filter function writing to the audit log, surfaced on a
  security page.
