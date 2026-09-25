---
title: Visible reasoning and a fail-closed approval gate
type: git-history
status: historical
date: 2026-09-08
commits: [07262ed, 8c7f204, d5dfbcf, aca731e]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
---

# Visible reasoning and a fail-closed approval gate

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `07262ed` | 2026-09-08 | Yash Kumar Singh | Expose each agent's reasoning instead of only counting characters |
| `8c7f204` | 2026-09-08 | Yash Kumar Singh | Render collapsible labels as plain text |
| `d5dfbcf` | 2026-09-08 | Yash Kumar Singh | Replace upstream branding and restructure the agent output |
| `aca731e` | 2026-09-08 | Yash Kumar Singh | Make the approval gate fail closed and theme the provenance output |

## Summary

Each answer began to show what every agent did and why. The approval gate
changed from a confirm dialog to a typed word.

## Why it changed

- The trace said only "FRIDAY produced analysis (849 chars)", which proved
  that something ran but showed none of the reasoning (`07262ed`).
- `qwen3` emits `<think>` blocks, and they were flowing into deliverables
  (`07262ed`).
- The confirm dialog accepted a stray Enter as approval (`aca731e`).

## Files changed

- `4ce/functions/orchestrator.py`
- `static/static/custom.css` (new, `aca731e`)
- `4ce/branding/make_assets.py` and the icon set (`d5dfbcf`; see
  [branding](2026-09-10-branding-and-first-run.md))

## Technical changes

- **Agent reasoning blocks** (`07262ed`). One expandable block per step: TONY's
  classification with the matched signals and the candidate routing table,
  then each agent's full output with its model and timing. `<think>` content is
  split out of the deliverable and shown separately, and unterminated blocks
  are treated as thinking.
- **Plain-text labels** (`8c7f204`). The markdown renderer escapes HTML inside
  `<summary>`, so literal `<b>` tags were showing.
- **Provenance table** (`d5dfbcf`). One table covering task type and signals,
  model and why, verdict, approval, per-agent timings and external calls,
  followed by collapsible reasoning.
- **Typed approval** (`aca731e`). The reviewer types APPROVE. An empty box, a
  wrong word, a cancel or a timeout withholds. Verified in the browser that an
  empty box withholds.
- **Stylesheet through the `custom.css` hook** (`aca731e`), so no Svelte
  component was modified at this point.

## Impact

Reasoning and approval, two of the core claims, became visible in the
interface. The approval design is recorded in
[ADR-0002](../decisions/0002-fail-closed-human-approval.md).

## Related documentation

- [AGENT_CHAIN.md - HUMAN](../AGENT_CHAIN.md#human---sign-off)
- [Timeline](README.md)
