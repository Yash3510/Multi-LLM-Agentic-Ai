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

Nothing to do: `install.py` attaches all five tools to the orchestrator, and
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
├── models.json             ← the model registry the router reads
├── test_tools.py           ← runs the test suite against a live instance
├── eval_retrieval.py       ← scores retrieval against a golden set of questions
├── eval_vision.py          ← scores the image reading pass against the answer keys
├── functions/
│   └── orchestrator.py     ← TONY / FRIDAY / JARVIS / ULTRON agent chain
└── tools/
    ├── sandbox.py          ← sandboxed Python execution via Docker
    ├── deliverables.py     ← .docx, .xlsx and .pptx output
    └── sovereignty.py      ← off-premise audit
```

---

## Adding a model

The router does not name models in code. `4ce/models.json` lists each model
with its modalities, capabilities, context, weights and licence, and says what
each task type needs - `code` needs `coding`, `vision` needs `vision`, and so
on. A task goes to the first served model that has what it needs.

To add one, load it in Bionic at a context that fits, add an entry, and run
`install.py`, which writes the file into the orchestrator:

```json
{
  "id": "prism-ml/bonsai-27b",
  "family": "Bonsai 27B",
  "modalities": ["text"],
  "capabilities": ["reasoning", "documents", "coding"],
  "context": 8192,
  "size_gb": 4.73,
  "licence": "check the model card"
}
```

It appears at once in every answer's routing line - chosen, "lacks coding",
or "not served" - and on the Sovereignty page under *Models on this machine*.
Order matters: the first capable, served entry wins, so put the model you
prefer for a capability above the others that have it. The chat picker and
preflight read the same file, so all three agree on what 4CE runs. A model
named in one of the orchestrator's `*_model` valves overrides the registry for
that task type, and the routing line says so.

---

## Making it physical

The Sovereignty page (the egress count in the navbar opens it) shows what the
workbench *was observed* connecting to. That is evidence, not a control: an
egress rule on the host is what makes a connection impossible, and the page's
**canary** is how you prove the rule works - it tries a handshake from the
backend to `1.1.1.1:443` and reports *Blocked* or *Reachable*.

The page lists the executables to name, under "Making it physical". Use those
paths, not guesses: on Windows the backend's network traffic comes from the
base Python interpreter, **not** `.venv\Scripts\python.exe`, which is only a
launcher.

### Windows (PowerShell, as administrator)

```powershell
New-NetFirewallRule -DisplayName "4CE backend: no egress" -Direction Outbound -Action Block -Program "<backend python.exe from the page>"
New-NetFirewallRule -DisplayName "4CE model server: no egress" -Direction Outbound -Action Block -Program "<Bionic.exe from the page>"
```

These block every outbound connection those programs make except on loopback,
which suits a single-box demo where the backend reaches Bionic on
`127.0.0.1:1234`. Then run the canary - it should read **Blocked** - and ask a
question in chat to confirm the model still answers. If the model server runs
on another machine, a program-wide block would cut the backend off from it;
restrict the rule to public addresses instead.

Remove them with `Remove-NetFirewallRule -DisplayName "4CE backend: no egress"`
(and the same for the model server).

### Linux (nftables)

A host-wide default-deny for new outbound connections, allowing loopback and
replies to the users of the UI:

```bash
sudo nft add table inet fource
sudo nft add chain inet fource out '{ type filter hook output priority 0; policy drop; }'
sudo nft add rule inet fource out oif lo accept
sudo nft add rule inet fource out ct state established,related accept
sudo nft add rule inet fource out counter log prefix '"4CE-DROP "' drop
```

`sudo nft delete table inet fource` removes it. The sandbox needs nothing: its
containers run with `--network none`.

### macOS

The built-in firewall filters incoming connections only. Blocking outgoing
ones needs `pf` rules or an application firewall; whichever you use, the
canary tells you whether it works.

### What the monitor found here

On its first run the monitor caught `Bionic.exe` opening a TLS connection to a
Cloudflare address (`[2606:4700:20::681a:799]:443`), with the configuration
audit reading 18 of 18. Bionic's own `settings.json` has
`"appUpdateChannel": "stable"` and `"autoUpdateExtensionPacks": true` - it
checks for updates by itself. Block it with the rule above, then press
**Start a new window** on the Sovereignty page so the count covers only what
follows.

---

## Measuring retrieval

`4ce/eval_retrieval.py` is a small golden set: fifteen questions about
SOP-MEC-014 and the P-101B readings, each with the clause text its answer has
to come from, and three questions the plant documents cannot answer.

```bash
cd backend && ../.venv/bin/python ../4ce/eval_retrieval.py      # Windows: ../.venv/Scripts/python.exe
```

It asks the running backend, checks the right passage is in the top four, then
applies the orchestrator's relevance guard and checks the guard kept it - and
that the unrelated questions, which vector search answers with its nearest
chunks regardless, come back empty. On this build: 15/15 found, 13 at rank 1,
15/15 kept, 3/3 unrelated emptied. Re-run it after changing the embedding
model, chunking, `retrieval_k` or the guard.

The guard is ported from 4CE's first prototype: a passage is only offered to
the agents when it shares a word of substance with the request, or when its
similarity is at least `retrieval_strong_score` (0.8). Asked "What is the
capital of France?", this knowledge base returns the seal leakage SOP at 0.68.

---

## Reading images

A scan, a handwritten note, a drawing or a photograph attached to a request is
read twice. First a reading pass asks the vision model for the image's fields as
JSON - each value or tag, its unit, how sure the model is, and the box on the
image it was read from. 4CE parses that, types each P&ID tag from its ISA 5.1
letters where it knows them (FE-101 is an instrument whatever the model filed
it under), draws the boxes on a copy numbered as the table is, and hands the
table to FRIDAY, who analyses the image with it. Readings go to the SOP rule
pack like a request's own. The table and the boxed copy go into the draft the
reviewer approves, the released answer and the Word report; anything read with
less than full confidence is marked **check** and listed under the checks, so
the reviewer compares it with its box before approving.

The size an image is sent at depends on what it is. The request's words decide
("P&ID", "drawing", "log", "scan"...), else whether it looks like paper:

| Kind | Sent at up to | Valve |
|---|---|---|
| Photograph | 900 px | `vision_max_edge` |
| Page or drawing | 2200 px | `vision_page_edge` |

`4ce/eval_vision.py` measures the reading pass against the two demo images'
answer keys, `4ce/demo/samples/shift_log_P-101_answer_key.txt` and
`pid_P-101_excerpt_answer_key.txt`:

```bash
cd backend && ../.venv/bin/python ../4ce/eval_vision.py --runs 3   # Windows: ../.venv/Scripts/python.exe
```

On this build, qwen3-vl-4b at an 8192 context, three runs at each size:

| Size | Handwritten log complete | Its smudged figure flagged | P&ID tags, of 15 | Time, log / P&ID |
|---|---|---|---|---|
| 900 px | 0 of 3 | 0 of 3 | 14.7 | ~11 s / ~17 s |
| 1400 px | 3 of 3 | 2 of 3 | 15.0 | ~11 s / ~36 s |
| 2200 px | 3 of 3 | 3 of 3 | 15.0 | ~11 s / ~31 s |

The flag rests on the model's own confidence, which varies run to run - that is
why every field carries its box. The boxes are approximate: on the handwritten
log they sit on the right line; on the P&ID most sit on or beside their tag and
one or two are a label away. Re-run the script after changing the vision model,
its context, the reading prompts or the valves.

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
