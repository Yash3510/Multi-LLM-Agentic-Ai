---
title: "apps/web: the full receipt"
type: log
status: implemented
owner: R3
updated: 2026-11-26
date: 2026-11-26
branch: wp/WP-UI-03-receipt
pr: 11
work_package: WP-UI-03
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: the full receipt

## What changed

- **The receipt's whole record** ([WP-UI-03, part 1](../../../architecture/frontend.md#wp-ui-03-part-1-the-full-receipt)):
  - `Receipt` gains the classification, the pack with its hash, the routing table, the skills and the ledger position;
  - the details panel shows them in a new Receipt tab, in the chat and the run view: the fingerprint short, whole on Show all and copyable, and who decided and when, with the time zone.
- **One working time:** the fake sets the receipt's `seconds` from the run's stages, and the strip writes it as the status line does (12.2 s in both on `run-0142`, where the strip said 9 s).

## Why

web-screens.md lists what a receipt holds; the strip showed only part of it. Review of #9 asked for the receipt's working time and the status line to agree. Step 2 goes in pull requests under ~400 changed lines, so file cards and the audit sheet follow.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts`, `fake.ts`, `fake.test.ts` | the record's fields; the fake's stand-ins and working time |
| `apps/web/src/lib/ui/components/DetailsPanel.svelte`, `ReceiptStrip.svelte`, `ResponseMessage.svelte`, `signoff.test.ts` | the Receipt tab; the strip's working time; the chat passes the receipt |
| `apps/web/src/routes/runs/[runId]/+page.svelte`, `apps/web/e2e/run-view.spec.ts` | the run view passes the receipt; the browser test |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-02-return-with-reason` at `8eea69b`). Tests first, each failing before its change:

- `fake.test.ts` "gives the receipt the sealed record…": failed, then `src/lib/data/` 82 passed.
- `signoff.test.ts`: the Receipt tab test and the strip's `9.4s working` failed, then 11 passed.
- `e2e/run-view.spec.ts` "a released run's receipt gives the whole record…": failed (no Receipt tab), then the run view's tests 8 passed on desktop and tablet.

**Every check:** the results are added below once run on this branch.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets.

## Decisions

- The record goes in a Receipt tab of the details panel, so the strip stays the summary and nothing shows twice.
- The fake's record is neutral stand-ins: classification Internal, pack Core 1.0.0, no skills, ledger entry 1042.

## Docs updated

[Frontend](../../../architecture/frontend.md), [web data contract](../../../architecture/web-data-contract.md), [web screens](../../../architecture/web-screens.md), [design system](../../../architecture/design-system.md), [state](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

- Every fake receipt has the same fingerprint and ledger entry.
- A withheld or returned run has no receipt; its run view's Sign-off stage says who and why.
- Deliverables as file cards are part 2; the QR code and evidence pack are M2.
