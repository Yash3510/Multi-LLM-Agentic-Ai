---
title: "Repository layout and working rules"
type: adr
status: implemented
owner: R1
updated: 2026-10-12
covers: []
tags: [4ce, adr, repository]
number: 29
decision_status: proposed
superseded_by: null
---

# ADR-0029: Repository layout and working rules

## Context

Four part-time people, each possibly with a different coding agent, on Windows, macOS and Linux, will add packages, packs and docs for years. Review attention is the scarce resource. Without one obvious home for every file and one way of working, the repository drifts and reviews slow down. Master plan §6.4 and §6.5 set the rules; this record decides how they are enforced.

## Decision

1. **One monorepo with a fixed layout,** described on [the repository page](../architecture/repository.md). The root holds only the listed entries.
2. **uv for everything Python;** pip is never used and no non-uv dependency file is committed. One `uv.lock`; `just setup` fails if it is out of date.
3. **One entry point:** every command is a `just` recipe that calls uv, so it runs the same in PowerShell and in a Unix shell. `just check` runs exactly what CI runs.
4. **Trunk-based branches, a small Conventional Commit for every finished step,** kept on `main` by rebase-merging, never squashed.
5. **The repo check enforces what can be checked:** the root allowlist, naming and banned words, packages with a README and tests, valid pack manifests, uv-only dependency files, no pip, no TODO without an issue, nothing over 1 MB outside Git LFS, and conventional, non-empty commits. It works from allowlists, so any tool's private instruction file is rejected without naming tools.
6. **Git hooks** (pre-commit) run the fast checks and gitleaks before each commit; CI runs `just check` on Linux, Windows and macOS.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Rules in a document only | They are forgotten under deadline; checks aren't |
| Squash merges | Lose the step-by-step history that shows how each change was made |
| A Makefile | Not native on Windows; just runs everywhere |

## Consequences

- Each new kind of file needs a home in the layout first; an unclear home is a structure question for review.
- Small deviations from the plan's text, found while building, are recorded in the work log: `.env.example` at the root, `.obsidian/templates.json`, and the scaffold templates kept in `tools/scaffold.py`.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R1.
