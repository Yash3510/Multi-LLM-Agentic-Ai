---
title: Preflight, runbooks and build reliability
type: git-history
status: historical
date: 2026-09-18
commits: [9ad0c59, 29d7923, b343de9, ac60463, 05f3574, f710855, 213f539, a3f5e3c, 4b8aa91, 992edfa, 52b927e, 8d6afea, b898277, 1d69f02]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - deployment
---

# Preflight, runbooks and build reliability

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `9ad0c59` | 2026-09-18 | Yash Kumar Singh | Add a preflight check for the state a demo actually depends on |
| `29d7923` | 2026-09-18 | Yash Kumar Singh | Write down the demo, including what not to demonstrate |
| `b343de9` | 2026-09-19 | Yash Kumar Singh | Stop preflight printing a traceback above a passing report |
| `ac60463` | 2026-09-19 | Yash Kumar Singh | Name the model server Bionic in the docs |
| `05f3574` | 2026-09-19 | Yash Kumar Singh | Rewrite the demo notes against what the build now measures |
| `f710855` | 2026-09-20 | Yash Kumar Singh | Stop the setup notes sending the operator somewhere the model is not |
| `213f539` | 2026-09-20 | Yash Kumar Singh | Say eighteen, and say what the extra seven cover |
| `a3f5e3c` | 2026-09-20 | Yash Kumar Singh | Check the chain can still be grounded, and say how to restore it |
| `4b8aa91` | 2026-09-20 | Yash Kumar Singh | Make the knowledge base rebuildable from the repository |
| `992edfa` | 2026-09-20 | Yash Kumar Singh | Let preflight check an instance other than the default |
| `52b927e` | 2026-09-20 | Yash Kumar Singh | Write the macOS setup down, and fix what it would have tripped over |
| `8d6afea` | 2026-09-24 | Yash Kumar Singh | Pin the macOS setup to Node 22 |
| `b898277` | 2026-09-24 | Yash Kumar Singh | Retry the Pyodide copy when Windows is still holding the file |
| `1d69f02` | 2026-09-24 | Yash Kumar Singh | Give the production build enough heap to finish |

## Summary

Everything a demo depends on became checkable in one command, and every
recovery became one command. The demo, the macOS setup and the recovery
procedures were written down against measured behaviour, and two build
failures were fixed.

## Why it changed

The model server had silently reloaded the vision model at 65,536 context and
evicted the small model after an hour idle. Nothing in the application showed
either (`9ad0c59`). The admin action *Reset vector DB* deletes every knowledge
record, and reindexing afterwards reports success while rebuilding nothing
(`a3f5e3c`).

## Files changed

- `4ce/preflight.py` (new, `9ad0c59`), `4ce/install.py`
- `4ce/docs/DEMO_SCRIPT.md` (new, `29d7923`), `4ce/docs/SETUP_MACOS.md` (new, `52b927e`), `4ce/docs/HOW_TO_RUN.md`
- `4ce/tools/sandbox.py` (`52b927e`)
- `scripts/prepare-pyodide.js` (`b898277`), `package.json` (`1d69f02`)

## Technical changes

- **Preflight** (`9ad0c59`, `a3f5e3c`, `992edfa`). Checks models and their
  context, Docker and the sandbox image, the backend, the plugins, tool
  attachment, the approval gate, the speech weights, and whether a knowledge
  base is attached. `--fix` loads the models correctly, and `--base` checks
  another instance. It decodes CLI output as UTF-8, so a passing report is no
  longer printed under a traceback on a cp1252 console (`b343de9`).
- **Knowledge base as code** (`4b8aa91`). `install.py` recreates *Plant SOPs*
  from `4ce/demo/samples/` and reattaches it. It was verified on a copy of the
  database after a reset.
- **Destructive admin actions documented** (`a3f5e3c`). Each one was tested on
  a copy of the database: Archive All, Delete All, Reindex, and Reset vector DB.
- **Docker environment on macOS** (`52b927e`). The sandbox's minimal
  environment dropped `HOME`, so the Docker client could not find its context.
  The allowlist now includes what the client needs.
- **Documentation fixes.** The model server is named Bionic (`ac60463`). The
  steps no longer send the operator to Workspace → Models, where a pipe
  correctly does not appear (`f710855`). The audit count reads eighteen
  (`213f539`). The macOS guide pins Node 22, because `engine-strict=true`
  refuses newer versions (`8d6afea`).
- **Build** (`b898277`, `1d69f02`). The Pyodide copy is retried on Windows
  sharing violations. `vite build` gets a 6 GB heap and completed in 2 m 8 s.

## Impact

Preflight gained its egress checks later, in `91152df`, and now has fourteen.
See [TESTING.md - preflight](../TESTING.md#preflight---preflightpy).

## Related documentation

- [HOW_TO_RUN.md](../HOW_TO_RUN.md)
- [SETUP_MACOS.md](../SETUP_MACOS.md)
- [DEMO_SCRIPT.md](../DEMO_SCRIPT.md)
- [Timeline](README.md)
