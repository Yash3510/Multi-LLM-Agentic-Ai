---
title: Foundation - the agent chain, the first tools and the sovereign configuration
type: git-history
status: historical
date: 2026-09-08
commits: [2646819, 5b76c67, 7267e6d, 2eee1a3, c256b89]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
---

# Foundation - the agent chain, the first tools and the sovereign configuration

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `2646819` | 2026-09-08 | Yash Kumar Singh | 4CE - sovereign on-premise agentic AI workbench (SIH PS 26117) |
| `5b76c67` | 2026-09-08 | Yash Kumar Singh | Add sovereign sandbox and Word deliverable tools |
| `7267e6d` | 2026-09-08 | Yash Kumar Singh | Add sovereignty audit tool and document the plugin set |
| `2eee1a3` | 2026-09-08 | Yash Kumar Singh | Point the router at the locally served models and add sovereign env template |
| `c256b89` | 2026-09-08 | Yash Kumar Singh | Fix three defects found by running the system end to end |

## Summary

The repository begins as a single root commit: the application platform plus
the first version of the 4CE layer. By the end of the day, the chain, three
tools, an installer and the air-gapped configuration existed and had been run
end to end against locally served models.

## Why it changed

The commit message states the aim: an agent layer that classifies, grounds,
produces, verifies and then asks a person, all on local models. The root
commit imports the platform without its history. The upstream licence is
retained in `LICENSE`, `LICENSE_HISTORY` and `LICENSE_NOTICE`.

## Files changed

- `4ce/functions/orchestrator.py` (393 lines at first)
- `4ce/tools/sandbox.py`, `4ce/tools/deliverables.py`, `4ce/tools/sovereignty.py`
- `4ce/install.py`, `4ce/env.sovereign.example`
- `4ce/README.md`, and the research notes now at [`deep-research.md`](../deep-research.md)

## Technical changes

- **Orchestrator** (`2646819`). A pipe function. TONY classifies and routes,
  FRIDAY grounds, JARVIS produces, ULTRON challenges, TONY replans once, and a
  human approval gate controls release. Progress is emitted as live status
  events.
- **Sandbox** (`5b76c67`). Runs generated Python in a disposable container
  with no network, a read-only root, dropped capabilities, no privilege
  escalation, and CPU, memory, process and time caps. It says so when Docker is
  unreachable rather than skipping execution.
- **Word deliverable** (`5b76c67`). A `.docx` with a classification banner,
  stored through the local file provider, built with `python-docx`, which was
  already a dependency.
- **Sovereignty audit** (`7267e6d`). Reads the running configuration and
  classifies every endpoint as on-premise or external. It states that it audits
  configuration, not packets.
- **Local models** (`2eee1a3`). Router defaults set to the served identifiers.
  `qwen3-vl-4b` (3.33 GB) and `qwen3-1.7b` (1.14 GB) fit in 6 GB together.
  Embeddings go through the same local server, so no model is fetched from
  HuggingFace and `OFFLINE_MODE` is safe. The built-in code interpreter is
  disabled in favour of the container sandbox.
- **First end-to-end run** (`c256b89`) found three defects:
  - the orchestrator recorded "HUMAN approved" with no session to ask anyone,
    and now requires a live session and an explicit affirmative;
  - the audit reported a false FAIL for a local OpenAI-compatible embedding
    endpoint, and is now endpoint-aware (11/11);
  - the installer's unconditional toggle disabled the orchestrator on re-run,
    and now enables only when inactive.

## Impact

The architecture that everything later builds on. See
[ADR-0001](../decisions/0001-agent-chain-as-a-runtime-plugin.md).

## Related documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [AGENT_CHAIN.md](../AGENT_CHAIN.md)
- [Timeline](README.md)
