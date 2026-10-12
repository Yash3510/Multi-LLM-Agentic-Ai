---
title: State
type: state
status: active
owner: R1
updated: 2026-10-12
tags: [4ce, state]
---

# State

Where 4CE stands right now. Updated at the weekly planning and at every milestone.

## What works

- **Repository foundations:** root files, the uv workspace, the [justfile](../justfile), the [repo check](architecture/repository.md#checks) and the [neutrality check](architecture/repository.md#checks). Evidence: `just check` on Linux.
- **[`core/common`](../core/common/README.md):** typed settings. Evidence: `uv run pytest core/common`.
- **The knowledge base layout:** this index, the templates and the shared Obsidian settings.

## In progress

Phase 0 (master plan §11.2), on the `4ce-core` branch:

- the docs check, import-boundary rules, the licence gate and import scan
- CI, the pre-commit hooks and the GitHub templates
- the Compose stack for the bundled services, with the third-party bundle
- the Pack spec and Rule Pack spec JSON Schemas

## Open questions

- [ADR-0035](adr/0035-frontend-foundations.md) (frontend foundations) and [ADR-0036](adr/0036-mpl-build-tools-and-licence-mapping.md) (MPL-2.0 build tools) wait on R1 and R4. `apps/web` is on hold until they are decided.

## Next up

Finish Phase 0 and reach M0: one-command install, CI green, and `just setup` followed by `just check` passing on Windows, macOS and Linux.
