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
| Document parsing | In-process parsers by default; in offline mode they may not download a model while running |
| Code execution | A container on the host, with networking removed |
| Deliverables | Written to local storage |

The configuration that produces this is committed as
[`4ce/env.sovereign.example`](4ce/env.sovereign.example). `OFFLINE_MODE=true`
additionally sets `HF_HUB_OFFLINE=1` and disables the update check.

## What it does not cover

These are the honest limits. Each is a real gap, not a hedge.

**Egress is observed, but by sampling sockets, not by capturing packets.** Two
things answer "does anything leave the premises", and they are kept apart:

- *Assurance.* `tools/sovereignty.py` reads the configuration the server is
  running - endpoints, engines, feature flags - and classifies each surface as
  on-premise or external. It cannot see a socket nobody configured.
- *Observation.* `backend/open_webui/utils/fource_egress.py` samples the
  operating system's socket table every 250 ms and classifies every connection
  held by the workbench's own processes - the backend, the model server and
  the frontend, with their children - as loopback, LAN or internet. The
  Sovereignty page, the navbar indicator and every answer's receipt report
  what it counted.

What observation still cannot see, stated on the page as well: a connection
that opens and closes between two samples; DNS lookups, which the OS resolver
makes on a process's behalf; and anything outside that scope - the browser,
the operating system, other programs. A capture on the uplink closes those
gaps.

It has already earned its place. On its first run it caught the model server
itself - `Bionic.exe` - opening a TLS connection to a Cloudflare address, with
the configuration audit reading 18 of 18. Bionic checks for its own updates
(`appUpdateChannel`, `autoUpdateExtensionPacks` in its settings). No setting in
4CE could have shown that.

It caught a second one, in the backend this time. The first spreadsheet
uploaded went to the platform's document loader, the `unstructured` library,
which - finding spaCy's `en_core_web_sm` missing - downloaded the model's wheel
from github.com and installed it into site-packages while the upload was being
processed. The watch showed the backend reaching GitHub; the backend log showed
the install. On an air-gapped machine the same upload would have failed. In
offline mode 4CE now refuses that download
(`backend/open_webui/utils/fource_offline.py`): the attempt fails with the
reason and is written to the audit trail, and the configuration audit checks
the model is installed, so a machine without it is flagged before its first
upload rather than during it.

Observation shows what the workbench did; it does not stop anything. An egress
rule on the host does, and the canary on the Sovereignty page proves the rule
works. Both are in "Making it physical" in `4ce/docs/HOW_TO_RUN.md`.

**The audit trail is tamper-evident, not tamper-proof.** Every request's
entries - its sources, each model call and tool call with the SHA-256 of what
went in and out, each file written, the verdict, the approver and the released
answer's fingerprint - are appended to `DATA_DIR/4ce/audit.jsonl`, each sealed
with the hash of the one before (`backend/open_webui/utils/fource_audit.py`).
Changing or removing an entry breaks the chain, and the Sovereignty page and
preflight say where. Someone who can write the file can still rewrite the chain
from that point on; keep a copy of the head hash somewhere they cannot reach.

**File tools reach one folder.** `tools/files.py` and `tools/sheets.py` write
only inside the workspace folder, and only text files and workbook copies; a
path that resolves outside it is refused, overwriting keeps the earlier
version, and a spreadsheet's source is never changed. A formula that could
reach outside the workbook - a web service, an external link, DDE, a
hyperlink - is refused, because the copy is opened in Excel on a plant PC.

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
