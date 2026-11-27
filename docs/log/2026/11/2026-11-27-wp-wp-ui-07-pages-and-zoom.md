---
title: "apps/web: evidence pages, zoom and pan"
type: log
status: implemented
owner: R3
updated: 2026-11-27
date: 2026-11-27
branch: wp/WP-UI-07-pages-and-zoom
pr: 15
work_package: WP-UI-07
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: evidence pages, zoom and pan

## What changed

- **Page navigation** ([WP-UI-07, part 2](../../../architecture/frontend.md#wp-ui-07-part-2-pages-zoom-and-pan)): Previous page and Next page around "Page n of m", with the list following the page shown. `?page=` opens a page, and `?box=` the page its box is on.
- **Zoom and pan:** Zoom out and Zoom in, from 100 % (the page fits) to 400 %, keeping the centre where it was. Zoomed in, the page scrolls in its frame, so panning is the browser's own: wheel, trackpad, touch, scrollbar, or the arrow keys once a box has focus.
- **The fake's stored run reads a second page**, with two more observations, one of them unsure.

## Why

Step 3 of the plan's build order (web-screens.md, evidence review). Evidence review's second part was planned as one pull request; to land each under about 400 changed lines it goes in three, split by layer: this one (the viewer and the route), then Verify and Correct in the contract and the fake, then on the page.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/fake.ts`, `fake.test.ts` | the fake's second page |
| `apps/web/src/lib/ui/components/EvidenceViewer.svelte`, `evidence-viewer.test.ts` | pages, zoom and pan |
| `apps/web/src/routes/evidence/[evidenceId]/`, `e2e/evidence.spec.ts` | `?page=`, the browser tests |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-07-evidence-review` at `bffe054`). Tests first, each failing before its change:

- `fake.test.ts`, the stored run's evidence with two pages: failed (one page), then `src/lib/data/` 83 passed.
- `evidence-viewer.test.ts`, moving between pages and opening on one: 2 failed, then 5 passed. Zooming: failed (no Zoom in), then 6 passed.
- `e2e/evidence.spec.ts`, `?page=` and `?box=` on page 2, and zoomed in by keyboard with the arrow keys panning from a box: with part 1's tests, 8 passed on desktop and tablet.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets; browsers other than Chromium (the Playwright projects are Chromium only), so panning with the arrow keys in Safari and Firefox is unverified.

## Decisions

- Panning is the browser's own scrolling, not a drag handler: it works by pointer, touch and keyboard with no code, while a focusable or draggable `div` needs an ARIA role it doesn't have, and svelte-check stays at 0 warnings.
- No `+` and `-` shortcuts: Zoom out and Zoom in are buttons, so they already work by keyboard.
- When `?box=` and `?page=` disagree, the box's page opens; a page outside the evidence opens the first.

## Known limits and follow-ups

- Verify and Correct, and who verified each observation, come in parts 3 and 4.
- Selecting a row doesn't scroll its box into view when zoomed in.
- At fit, a page taller than the window needs the window scrolled to reach the bottom of its frame.
- From the review of #14: links built from a raw path with an id (seven in the app, such as the run view's evidence link) lose an id shaped like `(x)` and fail on one with `[x]`, because `appHref` resolves the path as a route; SvelteKit's `resolve` with params doesn't encode `?`, `#` or `%` either. Left for a follow-up across all seven.
