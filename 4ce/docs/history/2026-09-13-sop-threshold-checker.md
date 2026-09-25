---
title: The SOP threshold checker
type: git-history
status: historical
date: 2026-09-13
commits: [f2c1de6]
authors: [grizzly077]
tags:
  - 4ce
  - git-history
---

# The SOP threshold checker

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `f2c1de6` | 2026-09-13 | grizzly077 | Add SOP threshold checker tool |

## Summary

A fourth tool, `sop_check.py`. It assesses inspection readings against an
authored rule pack and returns a clause-cited fit-for-service verdict, with
every comparison done in code.

## Why it changed

Threshold arithmetic done by a model was the weakest link in the chain: it
looks right and is occasionally wrong. See the design document,
[SOP_THRESHOLD_PLAN.md](../SOP_THRESHOLD_PLAN.md#why-this-tool-exists).

## Files changed

- `4ce/tools/sop_check.py` (494 lines, new)
- `4ce/SOP_THRESHOLD_PLAN.md` (the design; now [`4ce/docs/SOP_THRESHOLD_PLAN.md`](../SOP_THRESHOLD_PLAN.md))
- `4ce/demo/samples/SOP-MEC-014_readings_P-101B.txt` (new)
- `4ce/install.py` (registers `ace_sop_check`), `4ce/test_tools.py` (20 checks), `4ce/README.md`

## Technical changes

- A generic engine over a JSON rule pack with four rule types: `band`,
  `categorical`, `margin` and `presence`. SOP-MEC-014 ships as the default pack.
- Fails closed: a missing reading is `NO DATA`, never `PASS`, and readings
  that match no rule are listed as not assessed.
- A range such as "3 to 4 drops per minute" is assessed at its worse end.

## Impact

At this commit the tool was installed but not yet reachable by the chain.
`fef00fe` connected it, and the orchestrator now calls it directly
([tool-using chain](2026-09-18-tool-using-chain.md)). It was later extended to
read "current" and "required" thickness (`11f9ac1`), to report a vibration
velocity it cannot assess (`7d5e304`), and to read a missing guard "bolt"
without failing a defect reported absent (`195cb9f`).

## Related documentation

- [ADR-0004](../decisions/0004-deterministic-tools-for-arithmetic.md)
- [Timeline](README.md)
