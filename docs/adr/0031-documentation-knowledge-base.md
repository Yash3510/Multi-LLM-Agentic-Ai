---
title: "Documentation as the knowledge base"
type: adr
status: implemented
owner: R1
updated: 2026-10-12
covers: []
tags: [4ce, adr, documentation]
number: 31
decision_status: proposed
superseded_by: null
---

# ADR-0031: Documentation as the project's knowledge base

## Context

4CE sells assurance: being able to show, months later, why something is the way it is. Its own project has to meet the same bar. Docs that live on laptops, repeat each other or drift from the code can't. Master plan §6.6 sets the rules; this record decides how they are enforced.

## Decision

1. **`docs/` is the knowledge base and the repository root is an Obsidian vault.** Links are relative markdown links, so every page reads the same in Obsidian and on GitHub.
2. **One canonical page per subject;** other pages link to it.
3. **Validated frontmatter on every page:** a controlled list of types, statuses, owners and tags, plus per-type fields.
4. **One work-log entry per PR,** pages under a change's `covers` updated in the same PR, and an ADR for any decision.
5. **The docs check enforces it:** frontmatter, links and heading anchors, orphans, names, state freshness, history coverage, and for a PR the work log, drift and untouched accepted ADRs. It runs in `just check` and before each commit.
6. **New pages start from templates** (`just new-doc`, or Obsidian's Templates).

The rules in full are on [the documentation page](../architecture/documentation.md).

## Alternatives considered

| Option | Why not |
| --- | --- |
| A wiki outside the repository | Drifts from the code and can't be checked in CI |
| Wikilinks | Don't work on GitHub |

## Consequences

- Every PR carries a little documentation work; the templates and checks keep it small.
- The PR-only rules need the target branch (`--base`), so they run in CI rather than in the pre-commit hook.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R1.
