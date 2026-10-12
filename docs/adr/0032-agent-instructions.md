---
title: "Agent instructions"
type: adr
status: implemented
owner: R1
updated: 2026-10-12
covers: []
tags: [4ce, adr, agents]
number: 32
decision_status: proposed
superseded_by: null
---

# ADR-0032: Agent instructions

## Context

Team members may use coding agents, each person possibly a different one. Each tool looks for its own instruction file, and agents left to themselves pad history, weaken checks or take actions only a person should take. Master plan §6.7 decides the rules.

## Decision

1. **One file, [`AGENTS.md`](../../AGENTS.md), at the root,** holds the rules every coding agent follows, whatever the tool. A package or pack may add a short `AGENTS.md` that adds rules but never relaxes the root ones.
2. **Tool-specific instruction or configuration files are never committed.** A developer whose tool wants another file name keeps a local pointer, excluded in their own `.git/info/exclude`. The repo check rejects committed ones through its allowlists.
3. **Human-only actions:** agents never merge, approve, push to `4ce-core`, force-push, sign anything, or change CI, branch protection, CODEOWNERS, the licence policy, the risk tiers or `AGENTS.md`.
4. **Least privilege:** a developer's normal repository access and nothing more; no production or customer environments, credentials or signing keys.
5. **No tool attribution** in commits, PRs, comments or docs. The person who opens the PR is its author and is accountable for every line.

## Alternatives considered

| Option | Why not |
| --- | --- |
| One instruction file per tool | The rules drift apart between tools |
| No agent rules | Agents would follow whatever their tool's defaults are |

## Consequences

- `AGENTS.md` stays under about 150 lines and points to the docs for detail.
- Changes to `AGENTS.md` go through a normal PR approved by R1 and R4.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R1 and R4.
