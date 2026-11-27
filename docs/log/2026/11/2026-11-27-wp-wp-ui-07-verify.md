---
title: "apps/web: Verify in evidence review"
type: log
status: implemented
owner: R3
updated: 2026-11-27
date: 2026-11-27
branch: wp/WP-UI-07-verify
pr: 16
work_package: WP-UI-07
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: Verify in evidence review

## What changed

- **Verifying in the contract** ([WP-UI-07, part 3](../../../architecture/frontend.md#wp-ui-07-part-3-verify)): `Observation.verified` (who and when) and `verifyObservation(evidenceId, observationId)`, which records the signed-in person and the time, keeps an earlier record, and refuses an unknown observation. The fake keeps its own copy of the evidence, so a verification lasts until the page reloads; the stored run's first observation arrives verified.
- **Verify in evidence review:** each row not yet verified has Verify, and a verified row says who verified it and when, with the `check` glyph. The page asks the data source, then loads the evidence again; a refusal shows as an error toast. Without a way to verify, the list is read-only.

## Why

Step 3 of the plan's build order (web-screens.md, evidence review: "verify or correct each observation before rules use it"). The review of #15 split the rest of evidence review by feature, so Verify comes before Correct (part 4).

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts`, `fake.ts`, `fake.test.ts` | verifying in the contract and the fake |
| `apps/web/src/lib/ui/components/EvidenceViewer.svelte`, `evidence-viewer.test.ts` | Verify, and who verified each observation |
| `apps/web/src/routes/evidence/[evidenceId]/+page.svelte`, `e2e/evidence.spec.ts` | the page asks the data source; the browser test |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-07-pages-and-zoom` at `1b6d9b3`). Tests first, each failing before its change:

- `fake.test.ts`, who verified and when, the first record kept, an unknown observation refused: failed (nothing verified), then `src/lib/data/` 84 passed.
- `evidence-viewer.test.ts`, Verify only on what isn't verified and only with a way to verify, and who verified the rest: failed (no "Verified by"), then 9 passed.
- `e2e/evidence.spec.ts`, Verify on the stored run's evidence, still shown after another page and back: failed with the page not passing a way to verify, then with the other evidence tests 10 passed on desktop and tablet.

**Every check,** each `just check` recipe run directly (`just` isn't installed here), all exit 0, on `d2f5fa1`:

- `lint`: 236 files already formatted, all checks passed, pyright 0 errors; `imports`: 14 contracts kept; `repo-check`, `neutrality`: nothing reported.
- `docs`: exit 0, and with `--base wp/WP-UI-07-pages-and-zoom`; `licences`: 78 components, 114 files scanned, 5 bundled services.
- `test`: 807 passed, 97 deselected. `web-lint`: ESLint, Prettier and design lint clean, svelte-check 1477 files, 0 errors, 1 warning (part 2's page region). `web-test`: 96 files, 600 tests; tools 16 tests. `web-e2e`: 38 passed.

**From the screenshots** (`d2f5fa1`): on a tablet, a selected row's tint stopped above its Verify button, which straddled the tint's edge. The whole item takes the tint now.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets.

## Decisions

- Verifying twice keeps the first record, so who verified first is never overwritten.
- The viewer takes `onverify` from the page rather than calling the data source: without it the list is read-only, as it will be for a sealed observation or a person who may only read.
- After a verify the page loads the evidence again (`invalidateAll`), as the workspace pages do, rather than patching its own copy.

## Known limits and follow-ups

- Correct comes in part 4.
- An observation a released assessment used should be sealed, read-only with who verified it; that waits for the assessment (WP-UI-08), as the fake doesn't yet say which observations an assessment used.
- Everyone signed in sees Verify. Who may verify (the Author and the Reviewer) is the server's call; the page will follow it once the contract carries the person's role on the run.
- The fake writes no `observation.verified` ledger entry; the backend will (WP-LG-01).
