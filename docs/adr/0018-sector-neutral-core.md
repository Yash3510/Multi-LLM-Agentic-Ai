---
title: "Sector-neutral core"
type: adr
status: implemented
owner: R1
updated: 2026-10-12
covers: []
tags: [4ce, adr, packs]
number: 18
decision_status: proposed
superseded_by: null
---

# ADR-0018: A sector-neutral core; industries as packs

## Context

4CE's first working code was written for one industry, and its keyword lists, document kinds, rules and report headings live in the code. The pitch is that the same engine serves any rulebook. If industry words stay in the core, every new industry is a code change and the claim is false. Master plan §4.2 and §6.1 decide the split.

## Decision

1. **No industry vocabulary, rule, document type or workflow lives in `core/` or `apps/`.** Every industry, and every department common to all industries, arrives as a pack.
2. **The neutrality check enforces it** in CI and before each commit: a maintained list of sector terms (`tools/neutrality-terms.txt`) must not appear in `core/` or `apps/`, in any identifier style, in contents or in paths.
3. **The rule of two:** the core gains a general mechanism only when two packs need it.
4. **The two-pack test** (Phase 1) runs the end-to-end suite against two unrelated packs on the same build.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Neutrality by review only | Words slip in under deadline; a check doesn't forget |
| Configuration flags per industry inside the core | The core would grow with every industry, the opposite of the goal |

## Consequences

- Porting today's code means moving every industrial word into the Industrial & Energy pack.
- Words that are also core concepts (asset, receipt, contract, clause, policy) are not on the list, so the check needs a human eye on new terms.
- Test fixtures in the core use neutral examples too.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R1.
