---
title: State
type: state
status: active
owner: R1
updated: 2026-10-24
tags: [4ce, state]
---

# State

Where 4CE stands right now. Updated at the weekly planning and at every milestone.

## What works

Phase 0's foundations, on `4ce-core`, the trunk of [Yash3510/Multi-LLM-Agentic-Ai](https://github.com/Yash3510/Multi-LLM-Agentic-Ai). Evidence: CI runs `just setup` and `just check` on fresh clones and is green on Linux, Windows and macOS (first green run 2026-10-12, at commit `2506b19`); the [work log](log/2026/10/2026-10-12-4ce-core.md) records the rest.

- **The repository and its checks:** the [layout and working rules](architecture/repository.md), enforced by the repo check, the neutrality check, the import contracts, the [docs check](architecture/documentation.md#the-docs-check), the [licence gate, import scan and bundle check](architecture/licences.md), gitleaks and the commit-message hook. `just sync` starts each session.
- **[`core/common`](../core/common/README.md):** typed settings.
- **[`core/packs`](../core/packs/README.md):** the draft Pack and Rule Pack JSON Schemas.
- **The [bundled services](architecture/services.md):** PostgreSQL, Redis, MinIO, Prometheus and Grafana start healthy with `just services`.
- **[`core/db`](../core/db/README.md):** the database layer on SQLite and PostgreSQL, forward-only migrations, the row-level security policies, and organisation scoping that refuses cross-organisation writes in code (ADR-0010).
- **[`core/identity`](../core/identity/README.md):** users, argon2id passwords, signed tokens (ADR-0038), sign-in with a lockout after repeated failures, and sign-out.
- **[`apps/server`](../apps/server/README.md):** the health, sign-in, session and sign-out endpoints, with CSRF protection and one error envelope.
- **The knowledge base:** this index, the templates, the shared Obsidian settings and seven proposed ADRs.

## In progress

**The backend and the database come first.** Database foundations (WP-F-06) and identity (WP-ID-01) are built and tested, towards Phase 0's "app with a login" as an API. Still to do in this slice: the server's command line and `just` recipes (with a selector event loop on Windows, so psycopg's async mode works there), a smoke test that starts the real server on all three CI systems, PostgreSQL tests for row-level security, and the docs pages.

**Known limits:** the PostgreSQL-only paths (row-level security, `UPDATE … RETURNING`, NUL and over-long values) aren't exercised in CI yet. Intel Macs build `cryptography` and `argon2-cffi-bindings` from source, because the lock has macOS arm64 wheels only.

**The frontend is on hold in this stream.** Pranay, the frontend owner, develops `apps/web` separately; the [frontend page](architecture/frontend.md) has everything needed to do that independently. The backend's API is the contract between the two: the frontend codes against its OpenAPI document (ADR-0035 §4).

## Open questions

- **ADR-0035 and ADR-0036** (frontend foundations; MPL-2.0 build tools) wait on R1 and R4, before `apps/web` and the npm side of the licence gate land on `4ce-core`.
- **The proposed ADRs** 0009, 0015, 0018, 0023, 0029, 0031 and 0032 need their owners' acceptance.
- **ADR-0025:** MinIO's patch source; options in [MinIO patch source](research/minio-patch-source.md).
- **CODEOWNERS:** which GitHub handle holds each of R1 to R4.
- **GitHub:** make `4ce-core` the default branch, so Dependabot and the issue and PR templates apply to it.
- **Legal review:** Grafana's image reports a build commit that isn't in its public repository.

## Next up

1. **Finish database foundations and identity (WP-F-06, WP-ID-01):** the command line, the server smoke test, the PostgreSQL row-level security tests and the docs.
2. **Licence gate (R4):** prefer a package's SPDX `License` field over its classifiers; until then certifi and httpx are approved as pinned exact versions.
3. **Then:** the job queue (WP-F-07), storage (WP-F-08), Redis wiring (WP-F-11), the ledger (WP-LG-01) and the domain model (WP-DM-01).
