---
title: "apps/web: deliverables as file cards"
type: log
status: implemented
owner: R3
updated: 2026-11-27
date: 2026-11-27
branch: wp/WP-UI-03-file-cards
pr: 12
work_package: WP-UI-03
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: deliverables as file cards

## What changed

- **`FileInfo`** describes one file as a file card shows it: name, kind, size, SHA-256, classification and state. `Receipt.deliverables` lists a run's documents, and the fake's runs produce one ready `docx`.
- **`FileCard`** ([WP-UI-03, part 2](../../../architecture/frontend.md#wp-ui-03-part-2-deliverables-as-file-cards)): the kind's file icon and a neutral type tag, the name, the size as the knowledge pages write it, the hash prefix and the classification, and the state until the file is ready.
- **Under the receipt:** the receipt strip lists the deliverables as file cards, in the chat and at the end of the run view.

## Why

web-screens.md shows a released run's documents as file cards under its receipt. The full receipt was split in two to keep each pull request under ~400 lines; this is the second half, before the audit sheet.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts`, `fake.ts`, `fake.test.ts` | `FileInfo`, `Receipt.deliverables`, the fake's file |
| `apps/web/src/lib/ui/components/FileCard.svelte`, `file-card.test.ts`, `ReceiptStrip.svelte`, `e2e/run-view.spec.ts` | the card, the cards under the receipt, the tests |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-03-receipt` at `73be992`). Tests first, each failing before its change:

- `fake.test.ts` "gives the receipt the sealed record…", now expecting the deliverable: failed, then `src/lib/data/` 82 passed.
- `file-card.test.ts`: failed (no component), then 2 passed.
- `e2e/run-view.spec.ts` "a released run's receipt gives its file…": failed (no card), then the run view's tests 8 passed on desktop and tablet.

**Every check,** each `just check` recipe run directly (`just` isn't installed here), all exit 0:

- `lint`: 232 files already formatted (134 Python, 98 Markdown), all checks passed, pyright 0 errors; `imports`: 14 contracts kept; `repo-check`, `neutrality`: nothing reported.
- `docs`: exit 0, and with `--base wp/WP-UI-03-receipt`; `licences`: 78 components, 114 files scanned, 5 bundled services.
- `test`: 807 passed, 97 deselected. `web-lint`: ESLint, Prettier and design lint clean, svelte-check 1464 files, 0 errors. `web-test`: 94 files, 586 tests; tools 16 tests. `web-e2e`: 26 passed.

**Review fix** (`9aa691c`, test first): the cards were keyed by hash, so two files with the same content would break the strip (`each_key_duplicate`). A test with two such files failed, then passed with the cards keyed by position. After the fix: `npm --prefix apps/web test` 94 files, 587 tests passed; svelte-check 0 errors; the run view's browser tests 8 passed. The full check above ran before the fix.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets.

## Decisions

- The cards sit in the receipt strip, which both pages already show, rather than in each page.
- A card has no open or download action: the fake has no file behind it.

## Docs updated

[Frontend](../../../architecture/frontend.md), [web data contract](../../../architecture/web-data-contract.md), [web screens](../../../architecture/web-screens.md), [design system](../../../architecture/design-system.md), [state](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

- Opening and downloading files wait for files from the server; upload progress waits for uploads (WP-UI-09).
- Every fake run produces the same file.
