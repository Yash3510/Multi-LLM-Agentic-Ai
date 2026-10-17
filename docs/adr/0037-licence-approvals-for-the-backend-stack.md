---
title: "Licence approvals for the backend stack"
type: adr
status: implemented
owner: R4
updated: 2026-10-17
covers: []
tags: [4ce, adr, licences]
number: 37
decision_status: proposed
superseded_by: null
---

# ADR-0037: Licence approvals for the backend stack

## Context

The backend stack the project lead chose on 2026-10-12 brings three licences that master plan Appendix A doesn't allow without review:

- **psycopg and psycopg-binary**, the PostgreSQL driver, are LGPL-3.0-only. Appendix A: "review required: only unmodified, as a separate process or dynamic link, and only after an ADR".
- **certifi**, the certificate bundle httpx loads, is MPL-2.0: the same rule.
- **cffi**, which argon2-cffi needs, is MIT-0: MIT without even the attribution clause, but not named in Appendix A, so the strict gate stops it.

## Decision

1. **psycopg and psycopg-binary are approved** under LGPL-3.0-only, used unmodified and loaded as libraries by 4CE's code; never vendored or changed. Their licence text ships with every image and update, and their source is the published PyPI release.
2. **certifi is approved** under MPL-2.0, used unmodified; its file-level copyleft never reaches 4CE's files.
3. **cffi is approved** under MIT-0.
4. **The licence gate enforces approvals per package:** `tools/licence-review.toml` lists each under `[[approved]]` with its exact licence and this ADR. If a package's licence changes, the approval lapses and the gate fails. Any other package with the same licence still fails.

## Alternatives considered

| Option | Why not |
| --- | --- |
| asyncpg (Apache-2.0) instead of psycopg | The project lead chose psycopg |
| Allow LGPL and MPL for every package | Too broad: each package needs its own look |
| Python's standard library instead of httpx | The project lead chose httpx |

## Consequences

- The notices bundle (a later work package) must include these licences.
- ADR-0036 (MPL-2.0 build tools, proposed) is unaffected: it is about tools that never ship; certifi ships.

## Status

Proposed on 2026-10-12, decided by the project lead. To be confirmed by R4.
