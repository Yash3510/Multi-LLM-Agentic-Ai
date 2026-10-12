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

Phase 0's foundations, on `4ce-core`, the trunk of [Yash3510/Multi-LLM-Agentic-Ai](https://github.com/Yash3510/Multi-LLM-Agentic-Ai). Evidence: CI runs `just setup` and `just check` on fresh clones and is green on Linux, Windows and macOS (first green run 2026-10-12, at commit `2506b19`); the [work log](log/2026/10/2026-10-12-4ce-core.md) records the rest.

- **The repository and its checks:** the [layout and working rules](architecture/repository.md), enforced by the repo check, the neutrality check, the import contracts, the [docs check](architecture/documentation.md#the-docs-check), the [licence gate, import scan and bundle check](architecture/licences.md), gitleaks and the commit-message hook. `just sync` starts each session.
- **[`core/common`](../core/common/README.md):** typed settings.
- **[`core/packs`](../core/packs/README.md):** the draft Pack and Rule Pack JSON Schemas.
- **The [bundled services](architecture/services.md):** PostgreSQL, Redis, MinIO, Prometheus and Grafana start healthy with `just dev`.
- **The knowledge base:** this index, the templates, the shared Obsidian settings and seven proposed ADRs.

## In progress

**The backend and the database come first.** The next work packages build the server and its PostgreSQL foundations, towards Phase 0's "app with a login" as an API.

**The frontend is on hold in this stream.** Pranay, the frontend owner, develops `apps/web` separately, following [ADR-0035](adr/0035-frontend-foundations.md) and the [design system](architecture/design-system.md). The backend's API is the contract between the two: the frontend codes against its OpenAPI document (ADR-0035 §4).

## Open questions

- **ADR-0035 and ADR-0036** (frontend foundations; MPL-2.0 build tools) wait on R1 and R4, before `apps/web` and the npm side of the licence gate land on `4ce-core`.
- **The proposed ADRs** 0009, 0015, 0018, 0023, 0029, 0031 and 0032 need their owners' acceptance.
- **ADR-0025:** MinIO's patch source; options in [MinIO patch source](research/minio-patch-source.md).
- **CODEOWNERS:** which GitHub handle holds each of R1 to R4.
- **GitHub:** make `4ce-core` the default branch, so Dependabot and the issue and PR templates apply to it.
- **Legal review:** Grafana's image reports a build commit that isn't in its public repository.

## Next up

1. **Database foundations (WP-F-06):** the PostgreSQL schema base, forward-only migrations and the row-level security scaffold.
2. **Identity (WP-ID-01):** users, argon2id passwords, sessions and CSRF, behind a login API in `apps/server`.
3. **Then:** the job queue (WP-F-07), storage (WP-F-08), Redis wiring (WP-F-11), the ledger (WP-LG-01) and the domain model (WP-DM-01).
