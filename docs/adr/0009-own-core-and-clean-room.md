---
title: "Own core and clean room"
type: adr
status: implemented
owner: R1
updated: 2026-10-12
covers: []
tags: [4ce, adr, licences]
number: 9
decision_status: proposed
superseded_by: null
---

# ADR-0009: Own core and clean room

## Context

Today's 4CE runs inside a fork of Open WebUI. ADR-0001 (in the fork) chose that fork. The fork's licence carries a branding clause, its code shapes every feature, and investors and government buyers will ask what 4CE owns. Master plan v3.8 §0 and §2 decide that 4CE owns every line of product code; this record writes that down and supersedes ADR-0001.

## Decision

1. **4CE owns every line of product code:** backend, runtime, UI, Pack Studio, installer, CLI, design system, data model, specs and packs.
2. **It is built from specifications** (the master plan, the 4CE docs and the ADRs), not from upstream source. Nobody keeps upstream code open while writing the equivalent 4CE module.
3. **Only code the team wrote is ported** (`4ce/`, the `fource_*` backend files, the team's Svelte components), and only after every upstream import is replaced by a 4CE interface. Nothing else is copied: no CSS, strings, icons, prompts, configuration names or schema.
4. **New history, in the same repository.** The owned rebuild lives on the `4ce-core` branch of [Yash3510/Multi-LLM-Agentic-Ai](https://github.com/Yash3510/Multi-LLM-Agentic-Ai), with its own history that shares nothing with the fork's, and `4ce-core` is its trunk. The project lead chose this over the master plan's new repository on 2026-10-12. The fork's branches (`main`, `4ce`, `4ce-production`) are never merged into `4ce-core`, and at M1 they are frozen with branch protection: archiving the whole repository would freeze `4ce-core` too.
5. **Before the first external release,** a code-similarity scan against Open WebUI runs and its result is recorded in an ADR.
6. **Dependencies are used, not owned:** permissive libraries and unmodified services behind 4CE's own interfaces, under the [licence policy](../architecture/licences.md).

## Alternatives considered

| Option | Why not |
| --- | --- |
| Keep building on the fork | The branding clause, upstream's shape on every feature, and no clear ownership story for buyers |
| Port everything, then clean up | Upstream code would leak in; a clean room has to start clean |
| A new repository (the master plan's choice) | The project lead chose to keep 4CE in the existing repository, on its own branch and history |

## Consequences

- Phase 0 and Phase 1 rebuild what the fork gave for free: login, chat, files, settings.
- The neutrality check, the licence gate and the import scan enforce parts of this from the first commit.
- The fork's code sits in the same repository, one branch away. The clean-room steps above (no upstream code open while writing, no copying, the similarity scan) carry the weight a separate repository would have.
- `4ce-core` should be GitHub's default branch, so that Dependabot and the issue and pull request templates apply to it.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R1.
