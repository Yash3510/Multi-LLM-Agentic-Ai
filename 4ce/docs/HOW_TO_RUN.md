# How to Run 4CE Locally

On macOS, follow [SETUP_MACOS.md](SETUP_MACOS.md) instead — a clean first
run from an empty machine, with the Docker and Bionic settings that differ
there. This page assumes the environment already exists.


## Prerequisites

- **Bionic** running with models loaded (serves on `http://localhost:1234`)
- **Conda** (Anaconda/Miniconda) installed
- The `owui` conda environment set up (one-time, see below)

---

## One-Time Setup

### 1. Create the conda environment

```bash
/opt/anaconda3/bin/conda create -n owui python=3.11 -y
```

### 2. Install Open WebUI

```bash
/opt/anaconda3/envs/owui/bin/pip install open-webui
```

### 3. Set up the environment config

```bash
cp env.sovereign.example .env
```

Edit `.env` if needed (e.g. change `WEBUI_SECRET_KEY`).

---

## Starting the Server

### 1. Make sure Bionic is running

Open Bionic and load your models. The config expects:
- A chat/vision model (e.g. `qwen3-vl-4b`)
- A small chat/coding model (e.g. `qwen3-1.7b`), which ULTRON uses so that
  verification does not run on the same weights as the work it is checking
- An embedding model (`text-embedding-nomic-embed-text-v1.5`)

**Load them at 8192 context, not more.** Bionic remembers a context length
per model and will reload a 4B model at 65,536 tokens given the chance. On a
6 GB card that key/value cache does not fit, the runtime spills it to system
memory, and nothing reports an error - the system is simply slow. Measured on
the same machine and the same prompt, a document task took 30 seconds at 8192
and over 400 at 65,536; a vision task took 36 seconds against more than twenty
minutes. Set the idle TTL to never, too, or an evicted model is reloaded
mid-demo.

Verify with:

```bash
curl http://localhost:1234/v1/models
```

### 2. Start Open WebUI

Run this from the `4ce/` folder:

```bash
/opt/anaconda3/envs/owui/bin/open-webui serve --port 8080
```

Or to run it in the background:

```bash
/opt/anaconda3/envs/owui/bin/open-webui serve --port 8080 > /tmp/owui.log 2>&1 &
```

Wait ~20 seconds for DB migrations to finish, then open:

**http://127.0.0.1:8080**

### 3. Install / refresh the 4CE plugins

Run this after every code change to the plugins:

```bash
/opt/anaconda3/envs/owui/bin/python install.py
```

This creates the admin account on first run, uploads the orchestrator and the
tools, and attaches the tools to the orchestrator's model so the agent chain can
call them. Without that last step the chain still answers, but it reasons
unaided: no threshold arithmetic, no sandboxed execution and no `.docx`.

### 4. Check the machine is actually ready

```bash
python 4ce/preflight.py          # report
python 4ce/preflight.py --fix    # also load the models the way 4CE needs

# --base checks a different instance, matching install.py
python 4ce/preflight.py --base http://127.0.0.1:8081
```

It checks the models are loaded at a context length that fits, Docker is up
with the sandbox image pulled, the backend answers, the plugins are installed
and attached, the approval gate is on, and the speech weights are cached. Run
it before demonstrating; every check in it exists because it failed once.

---

## Login

| Field    | Value                  |
|----------|------------------------|
| Email    | `admin@4ce.local`      |
| Password | `4ce-demo-password`    |

---

## Tools on the model

Nothing to do: `install.py` attaches all four tools to the orchestrator, and
preflight fails if they are missing. Without them the chain still answers, but
it reasons unaided — no threshold arithmetic, no sandboxed execution, no `.docx`.

To check, run `python 4ce/preflight.py` and look for **Tools attached**.

Do not look for the orchestrator under **Workspace → Models**. That page lists
only models derived from a base model, and the orchestrator is a pipe, so it is
correctly absent there. It appears in the chat model picker and under
**Settings → Admin → Models**.

---

## Stopping the Server

If running in the background, find and kill the process:

```bash
pkill -f "open-webui serve"
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `curl http://127.0.0.1:8080/health` returns nothing | Server still starting — wait 20–30 s |
| Models not showing in model picker | Check Bionic is running and `OPENAI_API_BASE_URL` in `.env` points to `http://localhost:1234/v1` |
| Vision requests time out | Reload the vision model in Bionic with a context length of ~8192 (reduces VRAM usage) |
| Plugin install fails | Make sure the server is up (`/health` returns 200) before running `install.py` |
| Sandbox tool fails | Docker must be running on the host (not inside a container). Pre-pull: `docker pull python:3.12-alpine` |

---

## File Reference

```
4ce/
├── .env                    ← your local config (copy of env.sovereign.example)
├── env.sovereign.example   ← template
├── install.py              ← uploads plugins to running instance
├── test_tools.py           ← runs the test suite against a live instance
├── functions/
│   └── orchestrator.py     ← TONY / FRIDAY / JARVIS / ULTRON agent chain
└── tools/
    ├── sandbox.py          ← sandboxed Python execution via Docker
    ├── deliverables.py     ← .docx output generator
    └── sovereignty.py      ← off-premise audit
```

---

## Recovering retrieval

`python 4ce/preflight.py` reports **Knowledge attached**. If that fails, the
chain answers from the model's own memory and the provenance table says
`Grounding: none` — the answer still reads like an informed one, which is why
this is checked rather than assumed.

The destructive admin actions were tested against a copy of the database, so
what each one does is known rather than guessed:

| Action | Effect | Recoverable |
|---|---|---|
| Data Controls → Archive All | archives every chat | yes, Unarchive All restores them |
| Data Controls → Delete All | deletes chats and messages; **knowledge and uploads survive** | no, but retrieval is unaffected |
| Documents → Reindex | re-embeds; retrieval verified identical afterwards | n/a, safe |
| Documents → **Reset vector DB** | wipes every vector **and deletes every knowledge record** | only by the steps below |

Reset is the dangerous one, and the obvious remedy does not work: reindexing
afterwards returns success three times and rebuilds nothing, because the
knowledge record it would reindex has itself been deleted.

The uploaded files survive, and the collection is defined in the repository, so
recovery is one command:

```bash
python 4ce/install.py
```

It recreates `Plant SOPs`, indexes `SOP-MEC-014_seal_leakage.txt` and
`SOP-MEC-014_readings_P-101B.txt` from `4ce/demo/samples/`, and attaches the
collection to the orchestrator - the rebuilt collection has a new id, so the
old attachment does not carry over on its own. An intact knowledge base is left
alone, so this is safe to run at any time.

Verified on a copy of the database: after a reset left 0 knowledge records and
0 vector collections, one run reported `'Plant SOPs' rebuilt, 2 file(s)
indexed` and retrieval returned to 3,244 characters with clauses 2.1 and 2.2
quoted, identical to before.
