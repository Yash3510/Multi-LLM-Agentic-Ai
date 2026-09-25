---
title: Routing by a model registry
type: git-history
status: historical
date: 2026-09-24
commits: [456e7f8]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - model
---

# Routing by a model registry

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `456e7f8` | 2026-09-24 | Yash Kumar Singh | Route by a model registry, so a new model is an entry, not code |

## Summary

`4ce/models.json` became the single list of models 4CE routes between. The
router, the chat picker and preflight all read it.

## Why it changed

The problem statement asks that new models be "addable later without
redesigning the system". Routing was five valves each naming a model.

## Files changed

- `4ce/models.json` (new), `4ce/functions/orchestrator.py`, `4ce/install.py`, `4ce/preflight.py`, `4ce/test_tools.py`
- `backend/open_webui/routers/fource.py` (`/models`), `src/lib/components/fource/Sovereignty.svelte`, `src/lib/apis/fource/index.ts`
- `4ce/docs/HOW_TO_RUN.md`, `4ce/docs/DEMO_SCRIPT.md`, `README.md`

## Technical changes

- The registry records each model's modalities, capabilities, context,
  weights and licence, and the capabilities each task type needs.
- The router picks the first served model that has the needed capabilities,
  and records every entry's standing.
- ULTRON's independent model is chosen from entries that can verify.
- `install.py` writes the file into the orchestrator's `model_registry` valve.
- The Sovereignty page lists the registry under *Models on this machine*.

## Impact

Routing is unchanged in effect: code and chat go to `qwen3-1.7b`, and
documents, scans and analysis go to `qwen3-vl-4b`. A test holds the built-in
copy of the registry to the file.

## Related documentation

- [ADR-0006](../decisions/0006-route-by-a-model-registry.md)
- [HOW_TO_RUN.md - Adding a model](../HOW_TO_RUN.md#adding-a-model)
- [Timeline](README.md)
