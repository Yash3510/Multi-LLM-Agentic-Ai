---
title: "A modular monolith on one database"
type: adr
status: implemented
owner: R1
updated: 2026-10-17
covers: []
tags: [4ce, adr]
number: 10
decision_status: proposed
superseded_by: null
---

# ADR-0010: A modular monolith on one database

## Context

Master plan §6.1 and §6.3 make 4CE one codebase on PostgreSQL. The plan's layout gives the database plumbing no package, and its rule is to write an ADR before code in that case. On 2026-10-12 the project lead also chose SQLite as the zero-setup default.

## Decision

1. **One codebase, one database per installation:** SQLite for zero-setup development and single-user demos; PostgreSQL 18 for every real installation.
2. **`core/db` owns engines, sessions and organisation scoping.** Every package's tables use its `Base` and `OrgScoped`.
3. **Organisations are separated twice.** In code on every engine (reads filtered, writes stamped, cross-organisation writes refused), and on PostgreSQL by row-level security on every organisation's table, enforced against an app role (`fource_app`) that is neither superuser nor able to bypass it (§7.4, §7.24).
4. **One Alembic history, in `apps/server`,** because migrations need every package's tables and `core/db` must not import the packages that import it. Migrations run on both engines (batch mode); each has a tested downgrade (§6.5).
5. **Features that need PostgreSQL say so** when they are built (`SKIP LOCKED` for the job queue, LISTEN/NOTIFY, full-text search, insert-only ledger triggers). SQLite is not a production engine.

## Alternatives considered

| Option | Why not |
| --- | --- |
| PostgreSQL only (the plan's original) | The project lead chose a zero-setup default |
| The database plumbing in `core/common` | `common` must stay dependency-light; a database package can be swapped behind its interface |
| Migrations inside `core/db` | `core/db` would import every package that imports it: a cycle |

## Consequences

- Tests run on SQLite everywhere and the PostgreSQL-only ones on Linux CI.
- A raw SQL query skips the code-level filter; on PostgreSQL row-level security still holds, on SQLite it doesn't, which is one reason SQLite isn't for production.

## Status

Proposed on 2026-10-12, decided by the project lead. To be accepted by R1.
