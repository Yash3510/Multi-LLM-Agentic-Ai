# Open WebUI — Deep Research for 4CE

**Subject:** `open-webui/open-webui` v0.11.3 (shallow clone, this repo)
**Purpose:** Establish exactly what we inherit by forking, where the seams are, and how 4CE's sovereign agentic workbench (SIH PS 26117) maps onto it.
**Method:** Direct source reading of this checkout. Line references are to files in this repo and are accurate as of the cloned commit.
**Status caveat:** This is *source-derived*, not runtime-verified. Section 17 lists what must be confirmed by actually running it.

---

## 1. Executive summary

Ten findings that should drive our decisions:

1. **This is an application platform, not a chat skin.** 32 API routers, a dynamic plugin runtime, RBAC with groups and access grants, a 15-backend vector store abstraction, Alembic migrations, and a Socket.IO realtime layer. `main.py` alone is 3,043 lines; `config.py` 3,244; `utils/middleware.py` 6,400.
2. **Four native extension mechanisms exist.** Functions (pipe/filter/action), Tools, Pipelines (external sidecar), and MCP. Most of 4CE's agent layer can be added *as plugins* rather than by editing core files — which keeps us mergeable with upstream and drastically cuts integration risk.
3. **A "pipe" Function registers itself as a selectable model.** This is the single most important seam: our TONY orchestrator can appear in the model dropdown as `4CE / TONY` and intercept the whole conversation, with zero core modification (`functions.py:71-152`).
4. **Human-in-the-loop tool approval already ships.** `utils/tool_approval.py` implements pending/queued/requires_approval states and an `ask`/`full` approval mode. This is a native analogue of our Phase 5 approval gate.
5. **Subagent delegation already ships.** `utils/subagents.py` (702 lines) has a `delegate()` primitive with sync and async completion. Partially overlaps our JARVIS/FRIDAY/ULTRON runtime.
6. **Audit logging already ships** (`utils/audit.py`, 307 lines) plus a full event bus with webhooks (`events.py`, 1,273 lines).
7. **Code execution defaults to Pyodide in the browser — not a server-side sandbox.** This is a real gap versus our hardened `DockerSandbox`, and it matters for the SIH "sandboxed execution" criterion. See §8.
8. **Air-gap is genuinely achievable.** Chroma telemetry is already hard-disabled, fonts and Pyodide are served locally, and `OFFLINE_MODE=true` closes the remaining paths. Only **two** meaningful egress paths exist by default. See §12.
9. **Build needs internet; runtime does not.** Pyodide wheels and the embedding model are fetched at *build* time and frozen into the image. Plan the offline demo accordingly.
10. **Rebranding is licensed for our scale.** Clause 4 of `LICENSE` permits removing Open WebUI branding under 50 users in a rolling 30 days. Our demo qualifies. See §14.

---

## 2. Stack and repo anatomy

### Backend — Python / FastAPI

| Component | Version / detail |
|---|---|
| Framework | FastAPI 0.136.3, Uvicorn 0.51.0 |
| Validation | Pydantic 2.13.4 |
| Realtime | python-socketio 5.16.2 |
| ORM | SQLAlchemy (async sessions via `internal/db.py`) |
| Migrations | Alembic (`migrations/versions/`) |
| Auth | PyJWT, bcrypt/argon2, Authlib (OAuth/OIDC), SCIM |

### Frontend — SvelteKit

Vite + SvelteKit + TailwindCSS + TypeScript, i18n via i18next, Pyodide worker for in-browser Python.

### Directory map

```
backend/open_webui/
  main.py            # app assembly, router mounting (820-864), lifespan, version check (2569)
  config.py          # 3244 lines - every persisted setting + defaults
  env.py             # process-level env (OFFLINE_MODE 1176, WEBUI_NAME 936)
  functions.py       # pipe-function execution + model registration
  events.py          # event catalog, webhooks, event-function dispatch
  tasks.py           # background task registry
  routers/           # 32 routers, all mounted under /api/v1/*
  models/            # SQLAlchemy tables + pydantic forms (one file per entity)
  utils/             # middleware, plugin loader, tools, subagents, audit, RAG glue
  retrieval/
    loaders/         # document parsing (see §7)
    vector/dbs/      # 15 vector backends (chroma default)
    models/          # embedding model wrappers
    web/             # web search providers
  socket/            # Socket.IO server + event emitter factory
  migrations/        # Alembic
  internal/db.py     # engine/session
src/
  routes/(app)/      # SvelteKit pages: admin, workspace, c/[id], home, notes, ...
  lib/components/    # chat, admin, workspace, layout, common, icons
  lib/apis/          # typed fetch clients per backend router
  lib/stores/        # svelte stores (global state)
static/              # favicon, manifest, pyodide lock, sql.js, fonts
```

---

## 3. Runtime architecture — request lifecycle

A chat completion flows roughly like this (`utils/middleware.py` is the spine):

```
POST /api/chat/completions
  → auth (utils/auth.py: get_verified_user)
  → model resolution (utils/models.py) — is it a base model, a custom Model row, or a pipe function?
  → INLET filter functions (utils/filter.py: process_filter_functions, filter_type="inlet")
  → feature expansion in middleware.py:
        knowledge/RAG injection, web search, image gen,
        tool spec assembly (native or prompt-based function calling),
        memory, context compaction
  → dispatch:
        pipe function        → functions.py: generate_function_chat_completion
        ollama / openai      → routers/ollama.py | routers/openai.py
        pipelines            → routers/pipelines.py (external HTTP)
  → tool calling loop (utils/tools.py, 1789 lines) — may pause for approval (utils/tool_approval.py)
  → STREAM filter functions (per-chunk)
  → OUTLET filter functions (post-completion)
  → event emission over Socket.IO (socket/main.py: get_event_emitter)
  → persistence to chats table + audit (utils/audit.py)
```

**Key insight for 4CE:** we can attach at three different depths — inlet/outlet filter (cheap, cosmetic-to-moderate), pipe function (owns the whole turn — this is what we want for the agent loop), or core middleware edits (expensive, breaks upstream merges — avoid).

---

## 4. Extension points (the section that matters most)

### 4.1 Functions — in-process Python plugins

Functions are Python modules **stored in the database**, edited in the admin UI at `/admin/functions`, and loaded dynamically at call time by `utils/plugin.py:259` (`load_function_module_by_id`).

Three types:

| Type | Hook | Use for |
|---|---|---|
| `pipe` | Owns the entire completion; appears as a model | **TONY orchestrator, agent workflows** |
| `filter` | `inlet` (pre), `stream` (per-chunk), `outlet` (post) | Sovereignty guards, audit hooks, redaction, citation post-processing |
| `action` | Button on a message | "Generate approval note (DOCX)", "Send to reviewer" |

**Injected parameters** — the runtime inspects your function signature and injects only what you ask for (`functions.py:269-282`):

| Param | Meaning |
|---|---|
| `body` | The OpenAI-shaped request payload |
| `__user__` | User dict, including resolved `UserValves` |
| `__request__` | FastAPI `Request` — gives access to `request.app.state.config` |
| `__event_emitter__` | Async fn to push status/message/citation events to the UI |
| `__event_call__` | Async fn to *ask the user something and await the answer* (HITL!) |
| `__metadata__` | chat_id, message_id, session_id, features, tools |
| `__files__` | Attached files for this turn |
| `__tools__` | Resolved tool specs |
| `__task__` | Set when this is an internal task (title-gen etc.), not a user turn |

**Valves** — declare a `Valves` pydantic model and the admin UI auto-generates a settings form; `UserValves` does the same per-user (`utils/plugin.py:27-64`). This gives us a free config surface for things like model assignments per agent, approval thresholds, sandbox toggles.

**Minimal 4CE orchestrator pipe skeleton:**

```python
"""
title: 4CE Orchestrator
author: 4CE
version: 0.1.0
requirements: python-docx
"""
from pydantic import BaseModel, Field

class Pipe:
    class Valves(BaseModel):
        analysis_model: str = Field(default="qwen/qwen3-vl-4b")
        coding_model: str = Field(default="qwen2.5-coder:7b")
        require_approval: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):                      # manifold: one function -> many selectable models
        return [
            {"id": "tony", "name": "4CE / TONY (Orchestrator)"},
            {"id": "friday", "name": "4CE / FRIDAY (Analysis)"},
        ]

    async def pipe(self, body: dict, __user__: dict, __request__,
                   __event_emitter__, __event_call__, __metadata__: dict):
        await __event_emitter__({
            "type": "status",
            "data": {"action": "planning", "description": "TONY: classifying task", "done": False},
        })
        # ... route → execute → verify → (optionally) __event_call__ for approval
        return "final answer"
```

**Security note:** `utils/plugin.py:225` auto-installs pip packages declared in a function's frontmatter `requirements:` line. Anyone who can create a Function can install arbitrary packages into the backend. For a sovereign deployment this must be locked down (admin-only function creation is the default, but verify) and ideally disabled at the venue.

`ENABLE_PLUGINS` (imported in `routers/functions.py`) is the master switch.

### 4.2 Tools

Tools are Python classes exposed to the LLM as callable functions (`routers/tools.py`, `utils/tools.py` — 1,789 lines). Two calling modes: native function-calling and prompt-based for models without it. Tool servers can also be **external OpenAPI services** (`AddToolServerModal.svelte`).

This is where our `sovereign_ai/tools.py` equivalents land: `read_file`, `write_file`, `create_directory`, calculator, spreadsheet ops, DOCX generation.

### 4.3 Tool approval — native human-in-the-loop

`utils/tool_approval.py` (186 lines):

- Tool calls carry `status ∈ {pending, queued, requires_approval}` (`:57`, `:124`).
- `tool_approval_mode ∈ {ask, full}` on chat params, defaulting to `ask` (`:152-156`).
- `resolve_tool_call_output()` (`:20`) resumes a paused call once a human decides.
- `build_tool_approval_resume_payload()` (`:131`) rebuilds the request to continue.

**This is a direct native analogue of our Phase 5 approve/reject/request-changes gate**, already wired into the UI. Strongly prefer this over re-implementing our own approval flow in a fork.

### 4.4 Pipelines — external sidecar

`routers/pipelines.py` proxies to a separate Pipelines server over HTTP. Good for heavy/long-running work you don't want in the web process, and it's how you'd keep our existing Python codebase running as its own service. Cost: an extra container and an extra network hop (which must be shown as *internal* in the sovereignty demo).

### 4.5 MCP

`utils/mcp/` — Model Context Protocol client support, letting the app consume MCP tool servers. Useful later; not needed for a one-week demo.

### 4.6 Subagents

`utils/subagents.py` (702 lines) provides a `delegate()` primitive (`:270`), a default subagent system prompt (`:23`), internal-message processing (`:72`), and async delegation with an `[ASYNC SUBAGENT COMPLETE - {id}]` completion marker (`:553`). Config is read from `subagents.system_prompt` (`:454`).

Overlaps our JARVIS/FRIDAY/ULTRON runtime. Worth evaluating, but our own loop is more explicit about verification/replanning, so we may run our loop *inside* a single pipe rather than adopting this.

### 4.7 Skills, Automations, Events

- `routers/skills.py` + `models/skills.py` + `/workspace/skills` — reusable capability definitions.
- `routers/automations.py` + `/automations` route — scheduled/triggered runs.
- `events.py` — a typed event catalog (`EVENTS`, `:664`) with webhook dispatch, per-event filtering, and **event functions** (`dispatch_event_functions`, `:1103`). This is a clean place to hang audit/sovereignty side effects.

### 4.8 Decision matrix for 4CE

| 4CE capability | Best mechanism | Why |
|---|---|---|
| TONY orchestration + agent loop | **Pipe function (manifold)** | Owns the turn, emits status, appears as a model |
| Model auto-selection by task type | Inside the pipe + Valves | Judge-visible, configurable, no core edits |
| FRIDAY analysis / RAG grounding | Native knowledge + pipe | Reuse built-in retrieval, add our citation discipline |
| JARVIS tool execution | **Tools** | Native calling + approval integration |
| ULTRON verification | Step inside the pipe | Needs the replan loop; not a natural Tool |
| Human approval gate | **Native tool approval** + `__event_call__` | Already built and wired to UI |
| Deliverables (DOCX/XLSX/PPTX) | Tool + `utils/pdf_generator.py` pattern | Return file, surface via `files` event |
| Sandboxed code execution | **Replace engine** — see §8 | Pyodide default is not server-side isolation |
| Sovereignty audit / zero-egress proof | Filter function + `utils/audit.py` + events | Cheap to add, high demo value |
| Security dashboard | New SvelteKit route under `(app)/admin` | Follows existing admin page pattern |

---

## 5. Model layer and routing

Models come from three sources, unified in `utils/models.py`:

1. **Ollama** (`routers/ollama.py`) — native integration.
2. **OpenAI-compatible endpoints** (`routers/openai.py`) — `OPENAI_API_BASE_URL`. **This is how we point at LM Studio / Bionic Studio**, matching the endpoint our existing `local_provider.py` already speaks.
3. **Pipe functions** (`functions.py:71`) — plugins presenting as models.

Custom models are rows in the `model` table (`models/models.py:117`) with:
- `base_model_id` (`:124`) — proxying to an upstream model,
- `params` (`ModelParams`, `:72`) — temperature, system prompt, etc.,
- `meta` (`ModelMeta`, `:78`) — description, capabilities, attached knowledge/tools,
- `access_control` — group-based visibility.

**Implication for auto-routing:** we get a clean two-layer story for judges — a *declarative* layer (four 4CE agent models defined as rows, each pinned to an appropriate open-weight model with its own system prompt and toolset) and a *dynamic* layer (our pipe choosing among them per task). That is a materially stronger answer to the "automatic model selection" criterion than our current substring match in `router.py`.

---

## 6. RAG / knowledge subsystem

| Aspect | Detail |
|---|---|
| Vector DB | `VECTOR_DB`, default `chroma` (`config.py:501`); 15 backends incl. pgvector, milvus, qdrant, weaviate, elasticsearch |
| Embedding engine | `RAG_EMBEDDING_ENGINE`, default `''` = **local sentence-transformers** (`config.py:996`) |
| Embedding model | default `sentence-transformers/all-MiniLM-L6-v2` (`config.py:1002`) |
| Auto-update | `RAG_EMBEDDING_MODEL_AUTO_UPDATE` — **forced off by `OFFLINE_MODE`** (`config.py:1008`) |
| Reranking | `RAG_RERANKING_MODEL` + auto-update, same offline gating (`config.py:1035`) |
| Prompt template | `DEFAULT_RAG_TEMPLATE` (`config.py:1064`), overridable |
| Chunking / hybrid search | configurable in `config.py` RAG block |

The default stack (Chroma + local MiniLM embeddings) is **fully local**, which is exactly what we need. Knowledge collections are first-class (`routers/knowledge.py`, `/workspace/knowledge`) with per-collection access control — a good fit for "SOPs", "Inspection Reports", "Manuals" as separate collections.

Our `sovereign_ai/knowledge.py` grounding discipline (lexical-overlap guard against spurious semantic matches, latest-version-only citation) is **not** replicated here and is worth porting as a filter or as retrieval config tuning — it's a genuine quality edge we built.

---

## 7. Multimodal, OCR and document parsing

`retrieval/loaders/main.py` dispatches by extension (`_get_loader`, `:486`):

- Native: `PyPDFLoader`, `ExcelLoader` (`:103`), `PptxLoader` (`:171`), `CSVLoaderWithSummary` (`:156`), text with encoding detection (`:345`) and CJK handling (`:448`).
- `PDF_EXTRACT_IMAGES` default **False** (`config.py:998`).

Pluggable extraction engines via `CONTENT_EXTRACTION_ENGINE` (default `''` = native, `config.py:862`):

| Engine | Default endpoint | Sovereign? |
|---|---|---|
| Tika | `http://tika:9998` (`config.py:927`) | ✅ local container |
| Docling | `http://docling:5001` (`config.py:931`) | ✅ local container |
| MinerU | `local` mode, `http://localhost:8000` (`config.py:895-897`) | ✅ local |
| PaddleOCR-VL | `loaders/paddleocr_vl.py` | ✅ local (VL model) |
| Datalab Marker | cloud API key (`config.py:871`) | ❌ external — must stay disabled |
| Mistral OCR | `api.mistral.ai` | ❌ external — must stay disabled |
| External loader | `EXTERNAL_DOCUMENT_LOADER_URL` | depends |

**For scanned inspection reports and P&IDs**, the strongest sovereign options are Docling or PaddleOCR-VL as a local sidecar, or keeping our proven Tesseract path as a Tool. Note our existing `knowledge.py` OCR fallback chain (pypdf → tesseract → Dockerised tesseract) is more defensive than the native path and is worth preserving.

Vision/image understanding rides on the model layer — any vision-capable local model (our `qwen/qwen3-vl-4b`) works through the OpenAI-compatible connection.

---

## 8. Code execution — the real gap

Two related features, both **enabled by default**:

| Setting | Default | File |
|---|---|---|
| `ENABLE_CODE_EXECUTION` | `True` | `config.py:407` |
| `CODE_EXECUTION_ENGINE` | `pyodide` | `config.py:409` |
| `ENABLE_CODE_INTERPRETER` | `True` | `config.py:422` |
| `CODE_INTERPRETER_ENGINE` | `pyodide` | `config.py:431` |
| Jupyter alternative | `CODE_INTERPRETER_JUPYTER_URL` etc. | `config.py:435-450` |

`utils/code_interpreter.py` (197 lines) implements only the **Jupyter** executor (`JupyterCodeExecuter:25`, `execute_code_jupyter:192`). The default `pyodide` engine runs **in the user's browser** via WebAssembly.

**Why this matters for SIH:** Pyodide-in-browser is sandboxed *from the host* but it is not the server-side, network-disabled, resource-capped container isolation the problem statement implies, and it can't touch server-side files or produce server artifacts. Our existing `sovereign_ai/sandbox.py` is genuinely stronger — `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pids-limit 64`, memory/CPU caps, tmpfs, timeout.

**Recommendation:** expose our `DockerSandbox` as a 4CE **Tool** and use that for the demo's coding task, rather than relying on either built-in engine. It's a stronger claim, it's already written and tested, and it reuses work rather than discarding it. Optionally disable the built-ins to avoid a judge finding a second, weaker execution path.

---

## 9. Realtime events — the agent activity visualisation

`socket/main.py:1057` builds `__event_emitter__`; `:1181` builds `__event_call__` (which *awaits a user response* — the HITL primitive). Event types actually emitted by `utils/middleware.py`:

`chat:completion` (19), `output_text` (18), `status` (16), `message` (11), `text`, `image`, `reasoning`, `files`, `source`, `execute:tool`, `chat:message:error`, `chat:title`, `terminal:run_command`, `function_call`, `function_call_output`, …

**Status event shape** (verbatim pattern from `middleware.py:1504`):

```python
await __event_emitter__({
    "type": "status",
    "data": {"action": "web_search", "description": "Searching the web", "done": False},
})
```

This is exactly the mechanism for the live TONY → ROUTER → FRIDAY → RAG → JARVIS → ULTRON → APPROVAL pipeline visualisation — and because it's driven by real execution, it satisfies the architecture doc's "never fake execution activity" rule for free.

Citations surface through `source` events; generated deliverables through `files` events.

---

## 10. Auth, RBAC, access control

- `utils/auth.py` — `get_verified_user`, `get_admin_user` dependencies on every router.
- `models/users.py`, `models/groups.py`, `models/access_grants.py`, `utils/access_control/`.
- Per-resource `access_control` JSON on models/knowledge/tools/prompts — read/write by group.
- OAuth/OIDC (`utils/oauth.py`) and SCIM (`routers/scim.py`) for enterprise identity — a credible "fits PSU IT" talking point, though not needed for the demo.

This substantially exceeds our hand-rolled `auth.py` + `access_control.py` and is a clear win from the fork.

---

## 11. Persistence and migrations

- Engine/session in `internal/db.py`; async sessions (`get_async_session`).
- One file per entity in `models/` combining the SQLAlchemy table and pydantic forms.
- Alembic migrations in `migrations/versions/` — recent examples show the house pattern: `d4e5f6a7b8c9_add_automation_tables.py`, `f1e2d3c4b5a6_add_access_grant_table.py`.

**To add 4CE tables** (e.g. `4ce_task`, `4ce_task_step`, `4ce_approval`, `4ce_sovereignty_event`): add `models/four_ce.py` following the existing pattern and generate a migration in the same style. Keep the `4ce_` prefix so upstream merges never collide.

Alternatively — and faster for one week — persist agent-run state in the existing chat message metadata and Function valves, and only add tables if the demo actually needs queryable history.

---

## 12. Air-gap / sovereignty audit ← **the SIH proof section**

### Outbound paths that exist by default

| # | Path | Trigger | Kill switch |
|---|---|---|---|
| 1 | `api.github.com/repos/open-webui/open-webui/releases/latest` (`main.py:2569`) | Version update check on startup/UI | `ENABLE_VERSION_UPDATE_CHECK=false` (`env.py:1175`) — **also auto-disabled by `OFFLINE_MODE`** (`:1180`) |
| 2 | `huggingface.co` — downloads `sentence-transformers/all-MiniLM-L6-v2` | First embedding use, if not cached | `OFFLINE_MODE=true` sets `HF_HUB_OFFLINE=1` (`env.py:1179`); Docker image **pre-bakes** the model (`Dockerfile:148,157`) |
| 3 | `api.openai.com` | Only if an OpenAI connection is configured | Leave `OPENAI_API_KEY` empty; point `OPENAI_API_BASE_URL` at the local server |
| 4 | Web search providers (Brave, Serper, Tavily, …) | Only if web search enabled + key set | Off by default; keep disabled |
| 5 | Cloud OCR (Mistral, Datalab) | Only if selected as extraction engine | Default engine is local |
| 6 | `www.gravatar.com` | Explicit endpoint `/api/v1/utils/gravatar` (`routers/utils.py:23-25`) | Not on the signup path; avoid calling |
| 7 | `openwebui.com` community sharing | `ENABLE_COMMUNITY_SHARING` default **True** (`config.py:2110`) | Set `false` — removes share-to-community affordances |
| 8 | OTEL exporter | `ENABLE_OTEL` default **False** (`env.py:1238-1241`) | Already off |

### Already-safe by default

- **Chroma telemetry explicitly disabled** — `anonymized_telemetry: False` (`retrieval/vector/dbs/chroma.py:34`). Worth showing judges; it pre-empts the "but ChromaDB phones home" objection.
- **No external fonts or CDNs in `app.html`.** The only external URLs in the frontend are documentation `<a href>` links, not fetches.
- **Pyodide is served from our own origin.** `scripts/prepare-pyodide.js` downloads wheels at build time and freezes them into `pyodide-lock.json` so the browser loads packages "from the local server instead of fetching them from the internet" (`prepare-pyodide.js:130`).
- `sql.js` and all static assets are bundled.

### Recommended sovereign env block

```bash
OFFLINE_MODE=true                    # sets HF_HUB_OFFLINE=1, disables version check
ENABLE_VERSION_UPDATE_CHECK=false
ENABLE_COMMUNITY_SHARING=false
ENABLE_OTEL=false
OPENAI_API_BASE_URL=http://host.docker.internal:1234/v1   # local model server
OPENAI_API_KEY=
ENABLE_WEB_SEARCH=false
CONTENT_EXTRACTION_ENGINE=            # local, or 'docling' with a local sidecar
VECTOR_DB=chroma
RAG_EMBEDDING_ENGINE=                 # local sentence-transformers
```

### Demonstrating zero egress (stronger than logs alone)

The problem statement accepts "logs or a visible network monitor". Strongest available proof, in ascending order of persuasiveness:

1. Our audit-event counters (what `sovereign_ai/security.py` already does).
2. A 4CE filter Function that records every model/tool invocation with a `local: true` flag into an audit table, rendered on a security page.
3. **Run the container on a Docker network with no gateway** (`--internal` network) so egress is structurally impossible, and show `docker network inspect` plus a live `netstat`/Wireshark pane with zero external connections during the full demo run.

Option 3 is the one that ends the argument, and it's cheap — a compose-file change plus a terminal window. **Caveat:** with a fully internal network the local model server must also be reachable inside that network (run it as a container on the same network, or use a host-gateway alias), so this needs one rehearsal before demo day.

---

## 13. Deployment

- `Dockerfile`: multi-stage, `USE_CUDA` build arg (`:4`, `USE_CUDA_VER=cu128`), bakes the embedding model (`:148`, `:157`), sets `HF_HOME` and `SENTENCE_TRANSFORMERS_HOME` under `/app/backend/data/cache/embedding/models` (`:95`, `:102`).
- `docker-compose.yaml` bundles Ollama + app; variants exist for GPU (`docker-compose.gpu.yaml`), AMD, OTEL, Playwright, and API-only.
- Frontend build requires `npm run pyodide:fetch` first (wired into `dev` and `build` scripts).

**Practical demo plan:** build the image **with internet** ahead of time (models + Pyodide + wheels baked in), then run the demo offline. Do a full disconnected dry run at least 24 hours before the venue.

---

## 14. Licensing and branding

`LICENSE` is BSD-3-style plus **clause 4**: altering, removing, or replacing "Open WebUI" branding is prohibited **except** where (i) total end users ≤ 50 in any rolling 30-day period, (ii) written permission, or (iii) an enterprise licence.

Our SIH demo falls squarely under exemption (i), so the 4CE rebrand is permitted. `static/BRANDING.md` marks the branded asset surface (`favicon.png`, `opensearch.xml`, manifests).

Already changed in this fork: `package.json`/`pyproject.toml` name, `app.html` title, and `WEBUI_NAME` default with its forced `(Open WebUI)` suffix removed (`env.py:936`, originally lines 932-938).

Still branded and worth updating for the demo: `static/favicon.png`, `static/manifest.json`, `static/opensearch.xml`, `static/user.png`, splash/logo components, and `src/lib/constants.ts`.

**Attribution is still required** (clauses 1-2: retain copyright notice and disclaimer). Keep `LICENSE`, `LICENSE_HISTORY`, and `LICENSE_NOTICE` intact, and state the Open WebUI foundation openly in the SIH deck. Presenting a fork honestly as "built on Open WebUI, with our sovereign agentic layer" is both legally clean and, with judges who may recognise it, more credible than implying we wrote a chat UI from scratch.

---

## 15. Mapping our existing `sovereign_ai` work onto this fork

| Our component | LOC | Fate on 4CE | Effort |
|---|---|---|---|
| `agents.py` (Tony/Friday/Jarvis/Ultron) | 122 | **Port into a pipe function** — logic transfers almost verbatim | Low |
| `task_engine.py` (plan→route→execute→verify→replan→approve) | 278 | **Port into the pipe**; approval delegates to native tool approval | Medium |
| `router.py` (model selection) | 18 | **Rewrite properly** — use Model rows + Valves; current substring match is a liability | Low (and high value) |
| `sandbox.py` (hardened Docker) | 52 | **Keep as-is**, expose as a Tool — stronger than native Pyodide | Low |
| `knowledge.py` (parse/chunk/embed/cite) | 299 | **Mostly replaced** by native RAG; port the anti-hallucination citation guard | Medium |
| `tools.py` (file/calc/workspace ops) | 200 | **Port to native Tools** | Medium |
| `deliverables.py` (DOCX etc.) | 41 | Port as a Tool | Low |
| `security.py` + audit events | 18 | **Merge with native `utils/audit.py`**; add sovereignty counters | Low |
| `access_control.py` | 68 | **Replaced** by native RBAC/groups/access grants | Free |
| `auth.py`, `database.py`, `api.py`, `conversations.py`, `files.py` | ~460 | **Replaced** by the platform | Free |
| `ui.py` (Tkinter) + `web.py` | 472 | **Replaced** by SvelteKit | Free |
| `vector_store.py`, `embeddings.py` | 120 | **Replaced** by Chroma + local embeddings | Free |
| `docs/` (architecture + phase + verification docs) | — | **Keep** — this documentation set is a genuine scoring asset; retarget references to 4CE | Low |

Roughly **~1,200 of 2,624 lines are replaced by platform features**, and the ~700 lines that carry our actual differentiation (agent loop, verification/replan, hardened sandbox, citation discipline) port over as plugins.

---

## 16. Risks on a one-week runway

| Risk | Severity | Mitigation |
|---|---|---|
| Fork learning curve consumes the week | **High** | Stay in Python: pipe function + tools only. Touch SvelteKit only for the security dashboard, and only if time remains. |
| Native tool approval doesn't fit our replan loop | Medium | Fall back to `__event_call__` inside the pipe for the approval prompt |
| Offline build gotchas (Pyodide, HF, npm) surface at the venue | **High** | Build image with internet ≥24h early; full disconnected dry run |
| Judges perceive "reskinned open source" | Medium | Lead the pitch with the agentic/verification/sovereignty layer; be upfront about the foundation; show the diff |
| Two execution paths (Pyodide + our sandbox) confuses the sovereignty story | Low | Disable built-in code execution; demo only the hardened Docker tool |
| Losing the tested Phase 1-6 behaviour in translation | Medium | Port the loop wholesale; keep the existing repo intact and runnable as a fallback demo |

**Fallback worth preserving:** the existing `Multi-LLM-Docs` prototype is tested and works end to end. Do not delete or rewrite it. If the fork isn't demo-ready by day 5, that repo is the demo.

---

## 17. To verify at runtime (not yet confirmed from source)

1. Does the app start and connect to our LM Studio / Bionic endpoint via `OPENAI_API_BASE_URL`?
2. Does a trivial pipe function appear in the model dropdown end to end?
3. Do `status` events actually render as visible progress in the chat UI for a custom pipe?
4. Does `__event_call__` produce a usable approval prompt?
5. With `OFFLINE_MODE=true` and the network detached, does startup succeed with no stack traces (embeddings cached, no HF reach)?
6. Does Chroma initialise cleanly on first run in our environment?
7. Are Pyodide assets genuinely present post-build (`static/pyodide/` currently holds only the lock file pre-build)?
8. Is Function creation admin-only in practice (given `requirements:` auto-install)?

---

## 18. Quick file index

| Concern | File |
|---|---|
| App assembly, router mounting | `backend/open_webui/main.py:820-864` |
| Version check (egress) | `backend/open_webui/main.py:2569` |
| Env / offline flags | `backend/open_webui/env.py:1172-1180`, `:1238-1241` |
| Branding name | `backend/open_webui/env.py:936` |
| All persisted settings | `backend/open_webui/config.py` |
| Pipe execution + model registration | `backend/open_webui/functions.py:71-152`, `:269-282` |
| Plugin loading, valves, frontmatter installs | `backend/open_webui/utils/plugin.py:151-265` |
| Filters (inlet/stream/outlet) | `backend/open_webui/utils/filter.py:165-250` |
| Chat pipeline | `backend/open_webui/utils/middleware.py` |
| Tools runtime | `backend/open_webui/utils/tools.py` |
| Tool approval (HITL) | `backend/open_webui/utils/tool_approval.py` |
| Subagents | `backend/open_webui/utils/subagents.py:270` |
| Audit | `backend/open_webui/utils/audit.py` |
| Events / webhooks | `backend/open_webui/events.py:664`, `:1103` |
| Event emitter + user callback | `backend/open_webui/socket/main.py:1057`, `:1181` |
| Code interpreter (Jupyter) | `backend/open_webui/utils/code_interpreter.py:25`, `:192` |
| Document loaders | `backend/open_webui/retrieval/loaders/main.py:486` |
| Vector backends | `backend/open_webui/retrieval/vector/dbs/` |
| Custom model schema | `backend/open_webui/models/models.py:72-124` |
| Migrations | `backend/open_webui/migrations/versions/` |
| Frontend pages | `src/routes/(app)/` |
| Admin pages pattern | `src/routes/(app)/admin/*/+page.svelte` |
| Pyodide build step | `scripts/prepare-pyodide.js` |
| Licence + branding surface | `LICENSE`, `static/BRANDING.md` |

---

*Compiled 2026-09-08 from source at this checkout (v0.11.3). Re-verify line numbers after any upstream merge.*
