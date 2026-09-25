---
title: "ADR-0006: Route by a model registry"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - model
---

# ADR-0006: Route by a model registry

## Context

The problem statement asks that new open-weight models be "addable later
without redesigning the system". Routing was five valves each naming a model
for a task type, and the "candidates considered" line only echoed those names
(`456e7f8`).

## Decision

[`4ce/models.json`](../../models.json) is the registry. It holds each model's
modalities, capabilities, context, weights and licence, plus the capabilities
each task type needs. The router picks the first served model that has them,
and records every entry's standing (*chosen*, *lacks coding*, *not served*).

One file feeds three readers, so they cannot drift apart:

- the orchestrator, through its `model_registry` valve, which `install.py`
  writes;
- the chat model picker, which `install.py` restricts to the registry's
  models;
- `preflight.py`, which checks each model is loaded at its registry context.

The per-task `*_model` valves remain as overrides, and the routing line says
when one applied.

## Alternatives considered

- **Model names in valves**, the previous design, where adding a model meant
  editing configuration in several places.

## Consequences

- Adding a model is an entry in the file and one `install.py` run. It then
  appears in every answer's routing line and on the Sovereignty page under
  *Models on this machine*
  ([HOW_TO_RUN.md - Adding a model](../HOW_TO_RUN.md#adding-a-model)).
- Order matters: the first capable, served entry wins.
- A test holds the orchestrator's built-in copy of the registry to the file.

## Status

Accepted, `456e7f8` (2026-09-24).

## Related

- [AGENT_CHAIN.md - ROUTER](../AGENT_CHAIN.md#router---pick-the-model)
- [history/2026-09-24-model-registry.md](../history/2026-09-24-model-registry.md)
