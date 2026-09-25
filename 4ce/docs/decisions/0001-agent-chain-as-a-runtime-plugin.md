---
title: "ADR-0001: Build the agent chain as a runtime plugin"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - architecture
---

# ADR-0001: Build the agent chain as a runtime plugin

## Context

4CE needed a working application (authentication, chat, retrieval, file
storage, a realtime event channel) within about a week, and an agent layer on
top of it. The host platform offers several extension mechanisms. The one that
matters here is a *pipe function*: Python code, loaded at runtime, that
registers as a selectable model and owns the entire turn
([platform research §4](../deep-research.md#4-extension-points-the-section-that-matters-most)).

## Decision

Implement the orchestrator as a pipe function and each capability as a tool,
all under `4ce/`, deployed into a running instance by `install.py`. Edit the
platform's own code only where a plugin cannot reach.

## Alternatives considered

- **An external sidecar service** reached over HTTP. It keeps the agent code
  in its own process, but adds a container and a network hop that the
  sovereignty demonstration would then have to account for.
- **Modifying the platform's request middleware directly.** It gives full
  control, but every change becomes a merge conflict with the upstream code.

## Consequences

- The chain appears in the model picker as **4CE / TONY (Orchestrator)** with
  no core changes, and its configuration is rendered as a settings panel from
  the valves.
- Plugin ids had to be valid Python identifiers, hence `ace_*`, not `4ce_*`.
- Plugins run with the server's privileges ([SECURITY.md](../../../SECURITY.md)).
- The platform does not hand a pipe everything an ordinary model gets, which
  had to be worked around. Tools were unreachable until `pipe()` declared
  `__tools__` and the installer attached them (`fef00fe`). The platform's
  retrieval never reached the agents, so the chain now retrieves for itself
  (`09cc868`, `e1a0682`). Token usage went unrecorded until the pipe reported
  it (`e1a0682`).
- "Plugins only" did not hold for the interface or for egress observation:
  the sign-off panel, stage rail, Sovereignty page, egress watch and sign-off
  reconnection are core edits. They are listed in
  [ARCHITECTURE.md](../ARCHITECTURE.md#backend-additions---backendopen_webui).

## Status

Accepted, `2646819` (2026-09-08).

## Related

- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [history/2026-09-08-foundation.md](../history/2026-09-08-foundation.md)
