---
title: "ADR-0003: Verify on a different model"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - agent
---

# ADR-0003: Verify on a different model

## Context

Per-agent model valves were added blank, and blank meant "follow the routed
model" (`285c8ce`). So ULTRON graded JARVIS on the same weights and shared
every blind spot of the model it was checking. That is how an inverted
comparison survived verification: a 6.2 mm wall against a 6.0 mm retirement
limit was called a breach (`fef00fe`).

## Decision

A blank `ultron_model` valve crosses to a different served model, governed by
the `independent_verification` valve (on by default). Since `456e7f8` the
alternate is chosen from registry entries with the `verification` capability
first. With the current registry, code routes to `qwen3-1.7b` and ULTRON
checks on `qwen3-vl-4b`; documents route the other way.

## Alternatives considered

- **Same model, configurable.** This was the original default. Independence
  existed only after someone typed a model name, while the README already
  claimed it.

## Consequences

- Every verification costs a second model resident in memory. Both models fit
  in 6 GB at 8192 context ([ADR-0005](0005-load-models-at-8192-context.md)),
  but an evicted model means a reload on nearly every turn, which is why
  preflight checks both are loaded.
- A different model is not a correct model. The arithmetic and figure checks
  that do not depend on any model are in
  [ADR-0004](0004-deterministic-tools-for-arithmetic.md).

## Status

Accepted, `fef00fe` (2026-09-18). Registry-based selection since `456e7f8`.

## Related

- [AGENT_CHAIN.md - ROUTER](../AGENT_CHAIN.md#router---pick-the-model)
