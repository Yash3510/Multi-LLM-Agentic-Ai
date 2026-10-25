---
title: State
type: state
status: active
owner: R1
updated: 2026-10-25
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
- **[`core/ledger`](../core/ledger/README.md):** one insert-only hash chain per organisation; user creation, sign-in (every outcome) and sign-out write entries; `just ledger checkpoint` signs the head with the installation's Ed25519 key, `just ledger verify` finds edits, deletions, reordering and cut tails ([ledger](architecture/ledger.md), ADR-0014, ADR-0039).
- **[`apps/server`](../apps/server/README.md):** the health, sign-in, session and sign-out endpoints, with CSRF protection and one error envelope.
- **The server:** sign-in, session and sign-out over the API on SQLite or PostgreSQL ([api](architecture/api.md)); `just dev` runs it.
- **The knowledge base:** this index, the templates, the shared Obsidian settings and 14 proposed ADRs.

## In progress

**Backend slice 2, the evidence ledger, is built** (WP-LG-01, WP-LG-02): the `core/ledger` package, migration `0004` with insert-only triggers on both engines, a ledger entry for every identity action, the `ledger keygen`, `checkpoint` and `verify` commands, and a start-up refusal of a PostgreSQL role that bypasses row-level security. The [log entry](log/2026/10/2026-10-25-wp-lg-01-ledger.md) has the commands and results. A checkpoint is only as good as its outside copy: after `just ledger keygen` and `just ledger checkpoint`, keep the checkpoint file and the private key's backup off this machine.

**Backend slice 1 is built.** Database foundations (WP-F-06) and identity (WP-ID-01) give Phase 0's "app with a login" as an API: the `fource-server` command, `just dev`, a smoke test that starts the real server on all three CI systems, and PostgreSQL tests for row-level security that run in their own CI job. The [log entry](log/2026/10/2026-10-24-wp-id-01-identity-and-api.md) has the commands and results.

**Old `.env` after pulling:** `.env.example` changed (it now has `FOURCE_SECRET_KEY` and connects as `fource_app`). Delete your `.env` and re-run `just setup`, or copy the new lines from `.env.example`. The server must connect as `fource_app`, never as the owner, which bypasses row-level security. After pulling, also run `just migrate`: a database from before the ledger (`0003`) answers sign-in with `setup_incomplete` until it is migrated.

**Known limits:** PostgreSQL from a Windows host isn't exercised in CI (production runs on Linux). Intel Macs build `cryptography` and `argon2-cffi-bindings` from source, because the lock has macOS arm64 wheels only. The ledger's limits (the table owner between checkpoints, no key rotation, SQLite's `INSERT OR REPLACE`) are on the [ledger page](architecture/ledger.md#known-limits).

**The frontend is on hold in this stream.** Pranay, the frontend owner, develops `apps/web` separately; the [frontend page](architecture/frontend.md) has everything needed to do that independently. The backend's API is the contract between the two: the frontend codes against its OpenAPI document (ADR-0035 §4).

## Open questions

- **ADR-0035 and ADR-0036** (frontend foundations; MPL-2.0 build tools) wait on R1 and R4, before `apps/web` and the npm side of the licence gate land on `4ce-core`.
- **The proposed ADRs** 0009, 0010, 0014, 0015, 0018, 0023, 0029, 0031, 0032, 0035, 0036, 0037, 0038 and 0039 need their owners' acceptance.
- **Decided on 2026-10-24 by the project lead (no ledger question is open):** an unknown sign-in email is kept only as a keyed hash ([ADR-0039](adr/0039-every-action-writes-a-ledger-entry.md)); a scheduled job may sign checkpoints once the job queue lands, and people can still run `ledger checkpoint` ([ADR-0014](adr/0014-ledger-with-signed-checkpoints.md)).
- **ADR-0025:** MinIO's patch source; options in [MinIO patch source](research/minio-patch-source.md).
- **CODEOWNERS:** which GitHub handle holds each of R1 to R4.
- **GitHub:** make `4ce-core` the default branch, so Dependabot and the issue and PR templates apply to it.
- **Legal review:** Grafana's image reports a build commit that isn't in its public repository.

## Next up

1. **The job queue (WP-F-07),** which will also carry scheduled checkpoints; **Redis wiring (WP-F-11); storage (WP-F-08); the model gateway (WP-MD-01).**
2. **The pack loader (WP-PK-02),** then **route guards per role (WP-ID-02)** and **the domain model (WP-DM-01),** which depend on it.
3. **Licence gate (R4):** prefer a package's SPDX `License` field over its classifiers; until then certifi and httpx are approved as pinned exact versions.
