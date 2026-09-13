# How to Run 4CE Locally

## Prerequisites

- **LM Studio** running with models loaded (serves on `http://localhost:1234`)
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

### 1. Make sure LM Studio is running

Open LM Studio and load your models. The config expects:
- A chat/vision model (e.g. `qwen3-vl-4b`)
- An embedding model (`text-embedding-nomic-embed-text-v1.5`)

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

This creates the admin account on first run and uploads the orchestrator + tools.

---

## Login

| Field    | Value                  |
|----------|------------------------|
| Email    | `admin@4ce.local`      |
| Password | `4ce-demo-password`    |

---

## Enable Tools on the Model (one-time in UI)

1. Go to **Workspace → Models**
2. Find **4CE / TONY (Orchestrator)**
3. Enable these tools on it:
   - `4CE Sovereign Sandbox`
   - `4CE Deliverables`
   - `4CE Sovereignty Check`

Without this, JARVIS can classify and plan but cannot execute code or produce `.docx` files.

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
| Models not showing in model picker | Check LM Studio is running and `OPENAI_API_BASE_URL` in `.env` points to `http://localhost:1234/v1` |
| Vision requests time out | Reload the vision model in LM Studio with a context length of ~8192 (reduces VRAM usage) |
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
