# 4CE

**A sovereign, on-premise agentic AI workbench.** Every model call, every document
and every byte of context stays on hardware you control — no cloud API, no
telemetry, no data leaving the building.

Built for Smart India Hackathon PS 26117.

![4CE](4ce-screenshot.png)

---

## What it is

Most local-LLM front-ends give you a chat box. 4CE gives you an **agent chain with
a verification step and a human gate**, running entirely against a local model
server.

A single turn routes itself across multiple models by task type, grounds the answer
in your own documents, produces a deliverable, challenges that deliverable, and then
withholds it until a person approves.

```
TONY      classify the task (chat | code | vision | document | analysis)
ROUTER    pick the local model for that task type, and say why
FRIDAY    ground and analyse against local RAG
JARVIS    produce the deliverable
ULTRON    challenge it -> PASS / FAIL
TONY      replan once on FAIL, re-running FRIDAY and JARVIS
HUMAN     approve or reject before release
```

Every step is emitted as a live status event, so the chain is visible in the UI as
it actually executes — never simulated.

### Reasoning is shown, not claimed

Each answer carries an expandable **Agent reasoning** block per step: the task type
and the signals that matched it, the model chosen and the full candidate routing
table, each agent's output with its model and timing, and the model's own `<think>`
content stripped out of the deliverable and shown separately.

---

## Why it matters

| Property | How 4CE gets it |
|---|---|
| **Sovereign** | Local model server only. `OFFLINE_MODE=true`, no telemetry, no community sharing, no web search. |
| **Verified** | ULTRON challenges JARVIS's output and can force a replan. Run it on a *different* model so nothing grades its own work. |
| **Human-gated** | The approval dialog fails closed — an empty box, a wrong word, a cancel or a timeout all withhold the deliverable. |
| **Auditable** | An execution trace is appended to every answer. |
| **Multimodal** | Image parts are detected and routed to the vision model. |

---

## Quick start

Requires a local OpenAI-compatible model server (LM Studio, Bionic Studio) on
`http://localhost:1234`.

```bash
cp 4ce/env.sovereign.example .env
```

Start the backend, then load the plugin set:

```bash
python 4ce/install.py
```

Select **4CE / TONY (Orchestrator)** in the model picker, and enable the tools on
that model under **Workspace → Models**.

Full setup, configuration valves and troubleshooting: **[`4ce/HOW_TO_RUN.md`](4ce/HOW_TO_RUN.md)**

---

## The plugin set

Everything under [`4ce/`](4ce/) is this project's own code, loaded into the running
app at runtime.

| Component | What it does |
|---|---|
| [`functions/orchestrator.py`](4ce/functions/orchestrator.py) | The agent chain. Registers as a selectable model and owns the whole turn. |
| [`tools/sandbox.py`](4ce/tools/sandbox.py) | Runs generated Python in a disposable container — no network, read-only root, all capabilities dropped, hard CPU/memory/PID/time caps. |
| [`tools/deliverables.py`](4ce/tools/deliverables.py) | Renders agent output into a formatted `.docx` with a classification banner and reference table. |
| [`tools/sovereignty.py`](4ce/tools/sovereignty.py) | Audits live configuration for anything that could carry data off-premise, and returns a pass/fail table. |

See [`4ce/README.md`](4ce/README.md) for the valve reference and design notes.

---

## Verification status

Verified against a running instance with LM Studio serving `qwen3-vl-4b`,
`qwen3-1.7b` and `text-embedding-nomic-embed-text-v1.5`.

| Capability | Status |
|---|---|
| Model auto-selection across task types | Verified — coding routes to `qwen3-1.7b`, documents to `qwen3-vl-4b`, rationale shown |
| Per-agent model assignment | Verified — ULTRON runs on a different model from JARVIS |
| Agentic chain end to end | Verified — FRIDAY → JARVIS → ULTRON with a TONY replan on failure |
| Verification catches errors | Verified — ULTRON rejected fabricated inspection readings and forced a replan |
| Human approval | Verified — approve releases; reject and empty-box both withhold |
| Sandboxed code execution | Verified — 6/6 checks, including blocked network and enforced timeout |
| Word deliverables | Verified — 7/7 checks, valid OOXML |
| Sovereignty audit | Verified — 11/11 surfaces pass on the demo configuration |
| Local RAG | Verified — upload, embed, index and query in ~0.3 s |
| Multimodal / vision | **Not yet verified** — needs the vision model reloaded at ~8192 context; see [`4ce/README.md`](4ce/README.md) |

---

