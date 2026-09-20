# Running 4CE on macOS

A first run from a clean machine, start to finish. Works on Apple Silicon and
Intel. Everything runs locally: once the models are downloaded, the system does
not need the internet, which is the point of the project.

Budget about an hour, most of it waiting for model downloads.

---

## 1. What you need first

| | Why | Check |
|---|---|---|
| **Python 3.11 or 3.12** | the backend. **Not 3.13** — some dependencies have no wheels for it yet | `python3 --version` |
| **Node 18.13 – 22.x** | the frontend | `node --version` |
| **Bionic** | serves the open-weight models locally | opens, and Developer → server starts |
| **Docker Desktop** | the sandbox that runs generated code | `docker info` prints a version |
| **Git** | cloning | `git --version` |

Bionic is at [lmstudio.ai](https://lmstudio.ai) — it is the rebranded LM Studio,
so an existing LM Studio install works too. Docker Desktop is at
[docker.com](https://www.docker.com/products/docker-desktop/).

Homebrew covers the rest:

```bash
brew install python@3.12 node git
```

---

## 2. Get the code

```bash
git clone https://github.com/Yash3510/Multi-LLM-Agentic-Ai.git
cd Multi-LLM-Agentic-Ai
git branch --show-current     # should print: 4ce
```

A clone lands on `4ce` already, because that is the repository's default
branch. The check is worth doing anyway: a `main` branch also exists and is not
this project — if you end up on it, `git checkout 4ce`.

---

## 3. Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

On macOS the virtual environment's binaries are in `.venv/bin/`. Anywhere the
project's notes say `.venv/Scripts/python.exe`, that is the Windows spelling —
use `.venv/bin/python`.

---

## 4. Frontend dependencies

```bash
npm install
```

The first `npm run dev` also downloads a Pyodide bundle, so that one run needs
the internet even though nothing afterwards does.

---

## 5. Configuration

```bash
cp 4ce/env.sovereign.example .env
```

Open `.env` and change one line:

```
WEBUI_SECRET_KEY=change-me-before-the-demo
```

to anything else. The rest of the file is already set for local-only operation:
offline mode on, update checks off, telemetry off, web search off, and both
model and embedding endpoints pointed at Bionic on `localhost:1234`.

Do not add `FRONTEND_BUILD_DIR` — it is only for serving a production build.

---

## 6. Models in Bionic

Open Bionic and download three models:

| Model | Role |
|---|---|
| `qwen/qwen3-vl-4b` | documents, images, and verifying code answers |
| `qwen/qwen3-1.7b` | code, greetings, and verifying document answers |
| `text-embedding-nomic-embed-text-v1.5` | retrieval over the plant documents |

Then start the server: **Developer → Start Server**, port `1234`.

**Load the two chat models at 8192 context, not higher.** Bionic remembers a
context length per model and will happily reload a 4B at 65,536, which does not
fit and makes everything four to ten times slower with no error anywhere. Set
the idle TTL to never as well, or a model unloads mid-session and the next turn
pays to reload it.

Check it:

```bash
curl http://localhost:1234/v1/models
```

---

## 7. The sandbox image

```bash
docker pull python:3.12-alpine
```

Multi-arch, so it works on Apple Silicon without emulation.

**One macOS-specific setting.** In Docker Desktop → Settings → Advanced, enable
**"Allow the default Docker socket to be used"**. 4CE runs the `docker` CLI with
a deliberately minimal environment, and without that socket the client cannot
always find the daemon even though `docker` works fine in your terminal.

---

## 8. Start it

Two terminals, both from the repository root.

**Backend:**

```bash
source .venv/bin/activate
cd backend
../.venv/bin/python -m uvicorn open_webui.main:app --host 127.0.0.1 --port 8080
```

**Frontend:**

```bash
npm run dev
```

Give the backend about twenty seconds on its first run for database migrations.

---

## 9. Install the 4CE plugins

In a third terminal, from the repository root:

```bash
source .venv/bin/activate
cd 4ce
../.venv/bin/python install.py
```

This creates the admin account, uploads the orchestrator and the four tools,
attaches them to the model, restricts the model picker to the two models the
chain routes between, blanks the third-party endpoints Open WebUI ships
configured, and builds the `Plant SOPs` knowledge base from
`4ce/demo/samples/`. It is safe to re-run at any time — anything already correct
is left alone.

---

## 10. Check the machine is ready

```bash
python 4ce/preflight.py
```

Thirteen checks. It should end with **Ready.** If a model is loaded at the wrong
context length, `python 4ce/preflight.py --fix` reloads it at 8192.

Every check in that script exists because it failed once and cost real time to
diagnose, so do not skip it.

---

## 11. Sign in

**http://localhost:5173**

| | |
|---|---|
| Email | `admin@4ce.local` |
| Password | `4ce-demo-password` |

Change the password from Settings → Account if this is anything but a demo box.

The first page load in development mode compiles for roughly twenty-five
seconds. That is once, not every time.

---

## 12. Confirm it actually works

```bash
cd backend && ../.venv/bin/python ../4ce/test_tools.py
```

44 checks, all passing.

Then try these in the browser, in order:

1. **`hello`** — answers in a second or two with no agent chain. A multi-agent
   system that convenes a committee to say good morning is a liability, so TONY
   classifies first.
2. **"What is the acceptable mechanical seal leakage rate under SOP-MEC-014, and
   what must happen if it is exceeded?"** — quotes clause 2.1 and 2.2 from the
   indexed document. Check the provenance table's **Grounding** row: it reports
   the characters of retrieved text that actually reached the analysis agent.
3. **"Write a Python function that returns the median of a list and print it for
   [5, 3, 9, 1, 7]."** — the code runs in the container and the report shows a
   real exit code and real stdout, then asks you to approve before releasing the
   file.

`4ce/docs/DEMO_SCRIPT.md` has the full sequence with measured timings.

---

## When something is wrong

| Symptom | Cause |
|---|---|
| `Server Connection Error` in a reply | Bionic is not running, or its server was never started |
| Answers are correct but very slow | a model is loaded above 8192 context — `preflight.py --fix` |
| `returned no content — request (N tokens) exceeds the available context size` | a pasted document is too long. Attach it instead, so retrieval sends only the relevant passages |
| Sandbox says it is unavailable | Docker Desktop is not running, or the default socket setting in step 7 |
| `Grounding: none` on a document question | the knowledge base is gone. Re-run `python 4ce/install.py` — it rebuilds it |
| Preflight fails on **Knowledge attached** | same as above |

`4ce/docs/HOW_TO_RUN.md` has more, including how to recover from the admin
**Reset vector DB** action, which deletes more than it appears to.

---

## A note on hardware

The context and memory guidance in this project was measured on a 6 GB NVIDIA
laptop GPU. Apple Silicon shares memory between CPU and GPU, so a Mac with 16 GB
or more has considerably more headroom and may run comfortably above 8192.
Worth re-measuring rather than assuming the numbers transfer — but start at
8192, because that is the configuration everything here was verified against.
