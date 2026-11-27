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
- **Zoom and pan:** Zoom out and Zoom in, from 100 % (the page fits) to 400 %, keeping the centre where it was. Zoomed in, the page scrolls in its frame, so panning is the browser's own: wheel, trackpad, touch, scrollbar, or the arrow keys once the page or a box has focus. The page is a focusable region named for its page and zoom (review of #15).
- **The fake's stored run reads a second page**, with two more observations, one of them unsure.

## Why

Step 3 of the plan's build order (web-screens.md, evidence review). Evidence review's second part was planned as one pull request; to land each under about 400 changed lines it goes in three: this one, then Verify, then Correct.

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

**Every check,** each `just check` recipe run directly (`just` isn't installed here), all exit 0, on `5de53b1`:

- `lint`: 235 files already formatted, all checks passed, pyright 0 errors; `imports`: 14 contracts kept; `repo-check`, `neutrality`: nothing reported.
- `docs`: exit 0, and with `--base wp/WP-UI-07-evidence-review`; `licences`: 78 components, 114 files scanned, 5 bundled services.
- `test`: 807 passed, 97 deselected. `web-lint`: ESLint, Prettier and design lint clean, svelte-check 1477 files, 0 errors, 0 warnings. `web-test`: 96 files, 596 tests; tools 16 tests. `web-e2e`: 36 passed.

**svelte-check's warning** (`5de53b1`): the first full run showed one warning, the viewer reading its page prop outside `untrack`, which keeps only the first value. That is the intent, so the read moved inside `untrack`, and the run above has no warnings.

**Review fix** (`2d17cc7`, test first): the frame scrolled but couldn't take focus. A test that a zoomed page with nothing read is a focusable region named "Page 2 of 2, zoom 150%" failed (no region), then the viewer's 7 tests passed. svelte-check then reports one warning, `a11y_no_noninteractive_tabindex`, kept as above.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets; browsers other than Chromium (the Playwright projects are Chromium only), so panning with the arrow keys in Safari and Firefox is unverified.

## Decisions

- Panning is the browser's own scrolling, not a drag handler, so it works by pointer, touch and keyboard with no pointer code.
- The frame is a focusable region (review of #15): a scrolling region must take focus (axe's `scrollable-region-focusable`), so a page with nothing read still pans by keyboard. svelte-check warns that a region isn't interactive (`a11y_no_noninteractive_tabindex`); the warning stays, as the repository has no ignore comments, and an exception would need an ADR.
- No `+` and `-` shortcuts: Zoom out and Zoom in are buttons, so they already work by keyboard.
- When `?box=` and `?page=` disagree, the box's page opens; a page outside the evidence opens the first.

## Known limits and follow-ups

- Verify and Correct, and who verified each observation, come in parts 3 and 4.
- svelte-check reports one warning, `a11y_no_noninteractive_tabindex` on the page region, until an ADR decides an exception.
- Selecting a row doesn't scroll its box into view when zoomed in.
- At fit, a page taller than the window needs the window scrolled to reach the bottom of its frame.
- From the review of #14: links built from a raw path with an id (seven in the app, such as the run view's evidence link) lose an id shaped like `(x)` and fail on one with `[x]`, because `appHref` resolves the path as a route; SvelteKit's `resolve` with params doesn't encode `?`, `#` or `%` either. Left for a follow-up across all seven.
