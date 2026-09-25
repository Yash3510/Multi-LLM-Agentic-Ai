---
title: "ADR-0004: Arithmetic and checks run in code, not in a model"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - agent
---

# ADR-0004: Arithmetic and checks run in code, not in a model

## Context

A language model comparing a reading with a limit is the step that looks
right and is occasionally wrong. Observed: ULTRON read a 6.2 mm wall against a
6.0 mm retirement limit as a breach, forced a replan on that false premise,
and nothing was released after 130 seconds (`fef00fe`). A 1.7B verifier also
passed code whose claimed output had never been printed (`8559acc`).

## Decision

Where an answer depends on arithmetic, a threshold or a figure, code decides:

| Concern | Code that decides | Since |
|---|---|---|
| Reading against an SOP limit | `check_sop_thresholds`, an authored rule pack with clause citations | `f2c1de6` |
| Corrosion rate, remaining life, next inspection | `calculate_remaining_life`, every step with units | `11f9ac1` |
| Whether generated code worked | `_execution_check`, reading the sandbox's real exit code and output | `8559acc` |
| Whether a cited figure is in its source | `_figure_checks` | `b18f785` |
| Whether a figure attributed to the SOP exists anywhere | `_figure_checks`, "no citation, no claim" | `2b0d6c9` |

Tool results reach FRIDAY, JARVIS and ULTRON marked as authoritative. The
execution and figure checks can fail an answer that ULTRON passed.

## Alternatives considered

- **Let the models reason it out, and let ULTRON catch mistakes.** This was
  the original design. It failed as described above.
- **Learn thresholds from SOP prose with a model.** Rejected in the
  [rule-pack design](../SOP_THRESHOLD_PLAN.md#deliberately-out-of-scope),
  because it brings back the non-determinism the tool exists to remove.

## Consequences

- Rule packs must be authored and reviewed. Only SOP-MEC-014 ships.
- Anything the rule pack does not cover is reported as not assessed, and a
  missing reading as `NO DATA`, so a clean table never implies full coverage.
- Vibration given in mm/s is reported but not assessed: SOP-MEC-014 states
  vibration as ISO 10816 zones, whose boundaries depend on the machine class
  (`7d5e304`).

## Status

Accepted, `f2c1de6` (2026-09-13). Extended in `fef00fe`, `8559acc`,
`b18f785`, `11f9ac1` and `2b0d6c9`.

## Related

- [SOP_THRESHOLD_PLAN.md](../SOP_THRESHOLD_PLAN.md)
- [AGENT_CHAIN.md - deterministic steps](../AGENT_CHAIN.md#deterministic-steps---before-any-agent)
