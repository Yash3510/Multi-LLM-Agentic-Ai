---
title: "apps/web: the audit sheet"
type: log
status: implemented
owner: R3
updated: 2026-11-27
date: 2026-11-27
branch: wp/WP-UI-03-audit-sheet
pr: 13
work_package: WP-UI-03
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: the audit sheet

## What changed

- **`/runs/[runId]/audit`** ([WP-UI-03, part 3](../../../architecture/frontend.md#wp-ui-03-part-3-the-audit-sheet)), opened from the run view's Audit button. A decided run as a printed A4 record: the classification banner, the question, the static rail, the approval with the fingerprint in groups of four, the review shown with each check's sources, the record with the pack hash, and the footer with the print time, the printer and the ledger entry. On screen it's a preview with one Print button; a run not yet decided says so and links to its run view.
- **Both hashes whole and copyable** (review of #11): the Receipt tab gives the pack hash Show all and Copy like the fingerprint, in groups of four, with the format module's `formatHashFull`.
- **One date format:** the sheet and the Receipt tab write dates with the format module's `formatDateTime`, zone included.

## Why

web-screens.md and the design system's print rules define the audit sheet. It is the last of step 2's five pull requests.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/routes/runs/[runId]/audit/` (`+page.ts`, `+page.svelte`, `audit.test.ts`), `src/routes/runs/[runId]/+page.svelte`, `e2e/audit.spec.ts` | the sheet, the Audit button, the tests |
| `apps/web/src/lib/ui/components/DetailsPanel.svelte`, `signoff.test.ts`, `e2e/run-view.spec.ts` | both hashes whole and copyable; the format module's date |
| `docs/architecture/frontend.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-03-file-cards` at `2cc837d`). Tests first, each failing before its change:

- `signoff.test.ts`, the Receipt tab's two Show all buttons and grouped hashes: failed, then 12 passed.
- `audit.test.ts`, a run not yet decided: failed (no page), then passed.
- `e2e/audit.spec.ts`, the stored run's sheet from its run view: with the run view's tests, 10 passed on desktop and tablet.

**Every check,** each `just check` recipe run directly (`just` isn't installed here), all exit 0:

- `lint`: 233 files already formatted (134 Python, 99 Markdown), all checks passed, pyright 0 errors; `imports`: 14 contracts kept; `repo-check`, `neutrality`: nothing reported.
- `docs`: exit 0, and with `--base wp/WP-UI-03-file-cards`; `licences`: 78 components, 114 files scanned, 5 bundled services.
- `test`: 807 passed, 97 deselected. `web-lint`: ESLint, Prettier and design lint clean, svelte-check 1470 files, 0 errors. `web-test`: 95 files, 588 tests; tools 16 tests. `web-e2e`: 28 passed.

**In print:** the stored run's sheet was rendered with Playwright's print media and as an A4 PDF (`page.emulateMedia`, `page.pdf`, against the demo build). The first render showed two faults, both fixed: the Print button still painted, and the footer ran words together, because Svelte trims a block's leading space. The second render printed only the sheet, on one page.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets; printing on paper.

## Decisions

- The sheet's empty state is checked in a unit test: the demo can't reach an undecided run by its address, because the fake forgets asked runs on reload.
- The chat keeps its audit record dialog; the run view's Audit opens the sheet.

## Known limits and follow-ups

- The QR code in the footer waits for M2 (the QR step needs the owner's go).
- The 4CE mark stands in for the organisation's.
- `FileCard` writes sizes with the knowledge pages' `fileSize` (18.4 KB) while the format module has `formatBytes` (decimal kB); the design system wants one format module, so they should be unified.
