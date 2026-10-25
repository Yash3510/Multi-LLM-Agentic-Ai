---
title: Architecture overview
type: architecture
status: active
owner: R1
updated: 2026-10-25
tags: [4ce, architecture]
---

# Architecture overview

4CE is a self-hosted engine that turns an organisation's documents and rulebooks into decisions it can sign: grounded in its evidence, checked against its rules, approved by a named person, recorded as proof, and nothing leaves the building.

This page is the map. Each subsystem gets its own canonical page as it is built. Today the repository tooling, `core/common`, `core/db`, `core/identity`, `core/ledger`, `apps/server`, the draft specs in `core/packs` and the [bundled services](services.md) exist; everything marked _planned_ is design, not code.

## The universal loop

Every assured decision, in every industry, has the same shape:

```
 Evidence ──► Observations ──► Rules ──► Verdict ──► Sign-off ──► Record
 documents,   values with      authored,  PASS / REVIEW  named       evidence
 images,      units, source,   cited,     / FAIL /       person,     pack,
 data         page, box,       tested     NO DATA        fail-closed signed
              confidence                                             ledger
```

The models read the evidence and draft, explain and challenge the work. The rules decide. The person signs. The ledger remembers.

## One core, many packs

- **The core is sector-neutral.** No industry vocabulary, rule, document type or workflow lives in `core/` or `apps/`. The [neutrality check](repository.md#checks) enforces it.
- **Industries and departments arrive as packs:** vocabulary, document kinds, rules, calculators, workflows, persona layers, templates, policies, evals and demo data, mostly as configuration. Sector packs (Industrial & Energy, Banking & Lending, …) and cross-sector packs (Procurement, Finance & Expenses, Contracts, …) install side by side, namespaced.
- **Rule of two:** the core gains a general mechanism only when two packs need it.

## Principles

1. The assured run is the product: every request that produces work goes through it.
2. The core is sector-neutral.
3. Policy before access: permissions are worked out before any retrieval, tool call, model call, web fetch or export.
4. Deterministic wherever a rule exists: arithmetic, thresholds, dates, authority limits and unit conversions run in code.
5. Nothing unverified or unapproved is released by default. "Could not check" is never shown as a pass.
6. Everything is evidence: every step writes the hashes of its inputs and outputs to the ledger.
7. Declarative first: a pack is configuration by default.
8. Modular monolith: one codebase, two process roles (server and worker).
9. Adapters at every third-party edge.
10. Offline is the default state.

## System view (_planned_)

```
 Browser ── 4CE UI ──► 4ce-server (FastAPI) ──► 4ce-worker (1..N)
                         identity, policy,        assured run, evidence reading,
                         API, live events,        knowledge, rules, calc, verify,
                         sign-off, packs, admin   deliver, ledger, sovereignty
                              │                          │
        PostgreSQL (state, ledger, jobs, search) · Redis (live events, cache, locks)
        MinIO (originals, renders, deliverables) · model servers (OpenAI-compatible HTTP)
        sandbox (Docker + gVisor, no network) · Prometheus + Grafana (operations)
```

PostgreSQL, Redis, MinIO, Prometheus and Grafana run as unmodified separate services; 4CE talks to them over the network through its own interfaces.

## Subsystems

| Package | Responsibility | State |
| --- | --- | --- |
| [`core/common`](../../core/common/README.md) | Typed settings | built |
| [`core/db`](database.md) | Engines, sessions, organisation scoping, row-level security | built |
| [`core/packs`](../../core/packs/README.md) | Pack spec, loader, validator, signing, registry, namespacing | draft specs built; the rest _planned_ |
| [`apps/server`](api.md) | The API, the `fource-server` command, migrations | built |
| `core/domain` | Subjects, cases, evidence, observations, assessments | _planned_ |
| [`core/identity`](identity.md) | Users, passwords, tokens, lockout; route guards per role next, then groups, OIDC/SAML client | built (users, passwords, tokens, lockout) |
| `core/policy` | Policy store, evaluator, decisions, risk tiers | _planned_ |
| `core/models` | Model gateway, adapters, registry, hardware profiles | _planned_ |
| `core/knowledge` | Collections, ingest, PDF interface, Deep Cache, retrieval | _planned_ |
| `core/reading` | Evidence reading: document kinds, extraction, boxes | _planned_ |
| `core/rules` | The Rule Engine, rule pack spec, safe expressions, units | _planned_ |
| `core/calc` | Calculator engine | _planned_ |
| `core/runtime` | The assured run: stages, workflows, run store, events, budgets | _planned_ |
| `core/personas` | Role personas, prompt compiler, model prompt profiles, qualification | _planned_ |
| `core/skills` | Skill format, installer, validator, scanner, permissions, loading | _planned_ |
| `core/tools` | Tool broker, manifests, built-in tools, MCP client | _planned_ |
| `core/sandbox` | Runtimes, limits, artifacts | _planned_ |
| `core/verify` | Challenger, deterministic checks, citation alignment | _planned_ |
| `core/signoff` | Approvals, maker-checker, delegation | _planned_ |
| [`core/ledger`](ledger.md) | Insert-only chain per organisation, signed checkpoints, verifier; export next | built (chain, checkpoints, verifier) |
| `core/deliver` | Template engine, docx/xlsx/pptx renderers, fingerprints | _planned_ |
| `core/storage` | Storage interface; MinIO (S3) and local-filesystem adapters | _planned_ |
| `core/connectors` | Read-only data-source importers; cloud model connectors (off) | _planned_ |
| `core/i18n` | Locales, scripts, shared strings | _planned_ |
| `core/sovereignty` | Egress monitor, surface audit, offline guard, canary | _planned_ |
| `core/web` | Web broker and the Firecrawl adapter (off by default) | _planned_ |

The frontend's foundations are proposed in [ADR-0035](../adr/0035-frontend-foundations.md) and its design values in the [design system](design-system.md). Pranay, the frontend owner, develops it from the [frontend page](frontend.md); on `4ce-core` the backend and the database come first, and the server's OpenAPI document is the contract between the two.

## Related pages

- [Repository layout and working rules](repository.md)
- [Documentation rules](documentation.md)
- [Decision records](../adr/README.md)

## Decisions

[ADR-0009](../adr/0009-own-core-and-clean-room.md) (own core and clean room) and [ADR-0018](../adr/0018-sector-neutral-core.md) (a sector-neutral core).
