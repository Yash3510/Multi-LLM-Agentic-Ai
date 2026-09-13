# Security

4CE exists to handle material that must not leave a site. This document states
what that claim covers, what it does not, and where the trust boundaries sit. It
is deliberately specific: a sovereignty claim that cannot be checked is worth
nothing.

For vulnerabilities in the upstream platform itself, see Open WebUI's own
[`docs/SECURITY.md`](docs/SECURITY.md) and report them there.

## What "sovereign" means here

Every step that touches confidential content runs on the machine:

| Stage | Where it runs |
|---|---|
| Inference | A local OpenAI-compatible model server, over loopback |
| Embeddings | The same local server, so no model is fetched at runtime |
| Vector store | Chroma on local disk, with its own telemetry hard-disabled upstream |
| Document parsing | In-process parsers by default |
| Code execution | A container on the host, with networking removed |
| Deliverables | Written to local storage |

The configuration that produces this is committed as
[`4ce/env.sovereign.example`](4ce/env.sovereign.example). `OFFLINE_MODE=true`
additionally sets `HF_HUB_OFFLINE=1` and disables the update check.

## What it does not cover

These are the honest limits. Each is a real gap, not a hedge.

**The sovereignty audit reads configuration, not packets.** `tools/sovereignty.py`
inspects the endpoints and feature flags the server is actually running and
classifies each as on-premise or external. It cannot observe traffic. A process
could open a socket it never declared and the audit would not see it. For proof
rather than assurance, run the stack on a Docker network with no gateway, or
watch the host's adapter.

**Build time is not run time.** Producing the image needs the internet: npm
packages, Python wheels, Pyodide, and the frontend build. The air-gap claim
applies to a *built* system. Build first, then disconnect.

**The sandbox needs the backend on the host.** `tools/sandbox.py` shells out to
`docker`. If the backend itself runs in a container, the only way to reach the
daemon is to mount its socket, which grants that container full control of the
host's Docker — a worse position than the one the sandbox was added to improve.
Run the backend natively.

**Plugins execute with the server's privileges.** A function or tool is Python
loaded into the backend process. The upstream loader will also `pip install`
anything named in a plugin's `requirements:` frontmatter. Creating plugins is an
administrator action and should stay that way; treat adding one as equivalent to
deploying code.

**Model output is not evidence.** ULTRON challenges JARVIS's work and can force a
replan, and it has caught fabricated inspection readings in testing. It reduces
the rate of bad output; it does not make output trustworthy. Nothing is released
without a person approving it, and that gate is the actual control.

**Threshold decisions are arithmetic, deliberately.** `tools/sop_check.py`
compares readings against an authored rule pack in code, not by asking a model,
and cites the clause that decided each one. Where a reading is missing it returns
an incomplete assessment rather than a pass.

**Model weights are a supply chain.** 4CE runs whatever the local server serves.
The provenance of those weights is outside its control.

## Trust boundaries

| Boundary | Enforced by |
|---|---|
| Browser to backend | Session auth; first account is the administrator |
| User to user | Groups and per-resource access control |
| Generated code to host | `--network none`, read-only root, `--cap-drop ALL`, `--security-opt no-new-privileges`, PID/memory/CPU caps, wall-clock timeout, `tmpfs` scratch |
| Agent output to release | Human approval that fails closed — an empty box, a wrong word, a cancel or a timeout all withhold |

The sandbox flags above are verified by the test suite, including a case that
asserts an outbound request from inside the container fails.

## Hardening before real use

This repository is a competition submission, not a production deployment. Before
running it anywhere that matters:

- Change the administrator password. [`4ce/install.py`](4ce/install.py) carries a
  default one in plain text for reproducible demos.
- Set a real `WEBUI_SECRET_KEY`.
- Bind the backend to loopback, or put it behind a reverse proxy with TLS.
- Keep plugin creation restricted to administrators.
- Pre-pull the sandbox image; a missing image fails the run rather than silently
  skipping execution, but it fails at the worst moment.

## Reporting

Security issues in the 4CE layer — anything under `4ce/` — should be raised as an
issue on this repository. Issues in the upstream platform belong upstream.
