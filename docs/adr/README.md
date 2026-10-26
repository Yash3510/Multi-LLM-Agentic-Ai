---
title: Architecture decision records
type: index
status: active
owner: R1
updated: 2026-10-26
covers:
  - docs/adr/
tags: [4ce, adr]
---

# Architecture decision records

One record per decision, named `NNNN-kebab-title.md`. Once a record is accepted it is never edited, except to set `superseded_by`; a changed decision gets a new record (master plan §6.6).

Numbers 0009 to 0034 are reserved by the master plan (§15) for the decisions it lists. ADR-0001 to 0008 live in the archived fork; 0002 to 0008 are carried over when the code they govern is ported.

| ADR                                                 | Title                                                 | Decision status |
| --------------------------------------------------- | ----------------------------------------------------- | --------------- |
| [0009](0009-own-core-and-clean-room.md)             | Own core and clean room                               | proposed        |
| [0010](0010-modular-monolith-on-one-database.md)    | A modular monolith on one database                    | proposed        |
| [0014](0014-ledger-with-signed-checkpoints.md)      | Ledger with signed checkpoints                        | proposed        |
| [0015](0015-licence-allowlist-and-sbom-gate.md)     | Licence allowlist and SBOM gate                       | proposed        |
| [0018](0018-sector-neutral-core.md)                 | A sector-neutral core; industries as packs            | proposed        |
| [0023](0023-third-party-services.md)                | Third-party services: unmodified, separate, with source | proposed      |
| [0026](0026-redis-for-live-state.md) | Redis for live events, cache, locks and rate limits | proposed |
| [0029](0029-repository-layout-and-working-rules.md) | Repository layout and working rules                   | proposed        |
| [0031](0031-documentation-knowledge-base.md)        | Documentation as the project's knowledge base         | proposed        |
| [0032](0032-agent-instructions.md)                  | Agent instructions                                    | proposed        |
| [0035](0035-frontend-foundations.md)                | Frontend foundations                                  | proposed        |
| [0036](0036-mpl-build-tools-and-licence-mapping.md) | MPL-2.0 build and test tools, and the licence mapping | proposed        |
| [0037](0037-licence-approvals-for-the-backend-stack.md) | Licence approvals for the backend stack | proposed |
| [0038](0038-signed-tokens-for-sign-in.md) | Signed tokens for sign-in | proposed |
| [0039](0039-every-action-writes-a-ledger-entry.md) | Every action writes a ledger entry | proposed |
| [0040](0040-job-queue-on-postgresql.md) | Job queue on PostgreSQL | proposed |
