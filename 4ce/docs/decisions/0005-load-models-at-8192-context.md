---
title: "ADR-0005: Load the models at 8192 context"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - model
---

# ADR-0005: Load the models at 8192 context

## Context

The target machine has a 6 GB GPU. The model server remembers a context
length per model and will reload a 4B model at 65,536 tokens. That key/value
cache does not fit in VRAM, so the runtime spills it to system memory, and
nothing reports an error: the system is simply slow (`3bdee64`, `9ad0c59`).

Measured on the same machine and prompt (`327e143`):

| Task | 8192 context | 65,536 context |
|---|---|---|
| Document | 30 s | over 400 s |
| Vision | 36 s | over 20 minutes |

## Decision

Load both chat models at 8192 context, with the idle TTL set to never.
`qwen3-vl-4b` (3.33 GB) and `qwen3-1.7b` (1.14 GB) then stay resident together
(`2eee1a3`). The context is recorded per model in
[`models.json`](../../models.json), and `preflight.py --fix` reloads any model
found above it.

## Alternatives considered

- **The larger context** the server offered by default. Measured above.

## Consequences

- A document pasted into the prompt can exceed the context. The turn then
  fails with the server's own message, which names the problem and the fix
  (`cef4459`). The documented remedy is to attach the file, so retrieval sends
  only the relevant passages.
- Replies are capped per agent (`max_tokens`, 900), and images are downscaled
  before they reach the model, to keep a turn predictable (`5223fdb`).
  Photographs go at 900 px; since `195cb9f`, pages and drawings go at 2200 px,
  because handwriting lost readings at 900.
- Machines with more memory, such as Apple Silicon with unified memory, may
  run higher. That has not been measured
  ([SETUP_MACOS.md](../SETUP_MACOS.md#a-note-on-hardware)).

## Status

Accepted, `3bdee64` (2026-09-08). Enforced by preflight since `9ad0c59`.

## Related

- [HOW_TO_RUN.md](../HOW_TO_RUN.md)
- [TESTING.md - preflight](../TESTING.md#preflight---preflightpy)
