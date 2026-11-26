---
title: "apps/web: the sign-off page"
type: log
status: implemented
owner: R3
updated: 2026-11-26
date: 2026-11-26
branch: wp/WP-UI-02-sign-off-page
pr: 9
work_package: WP-UI-02
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: the sign-off page

## What changed

- **`/runs/[runId]/sign-off`** ([WP-UI-02, part 1](../../../architecture/frontend.md#wp-ui-02-part-1-the-sign-off-page)): the run view with the chat's sign-off panel docked while the run waits at the gate. Before the gate it says the panel opens there; after the decision it is the decided run view with its receipt.
- **One page, one run:** the run view's route moved under an optional segment, `[[panel=panel]]`, whose matcher (`src/params/panel.ts`) takes only `sign-off`. `/runs/[runId]` and `/runs/[runId]/sign-off` are the same page on the same run, so a decision taken there or in the chat shows in both.
- **Refusals:** a decision the source refuses (someone decided first) shows "Nothing was released" with the reason.
- **The link:** while the run waits, the run view's Sign-off stage offers Review and decide.

## Why

The plan gives sign-off its own page, the run view with the panel docked (web-screens.md, `/runs/[runId]/sign-off`), and the frontend owner decided on 2026-11-25 to keep the chat's panel as well, both on one run. The owner asked for step 2 in pull requests under ~400 changed lines each. Moving the route rather than extracting the run view into a component keeps this one small: git records the move as a rename, so only the changed lines count.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/params/panel.ts`, `panel.test.ts` | new: the matcher for the optional `sign-off` segment |
| `apps/web/src/routes/runs/[runId]/[[panel=panel]]/+page.svelte`, `+page.ts` | moved from `src/routes/runs/[runId]/`; the docked panel, the refusal, the Review and decide link |
| `apps/web/e2e/sign-off.spec.ts` | new: the sign-off page in the browser |
| `docs/architecture/frontend.md`, `web-screens.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, in the worktree used since WP-UI-05, on this branch (stacked on `wp/WP-UI-01-run-view` at `b707080`).

- **Test first:** `npx vitest run src/params/panel.test.ts` failed (`Failed to resolve import "./panel"`), then 1 passed.
- **In the browser:** `npx playwright test e2e/sign-off.spec.ts --project=desktop --project=tablet`. The first run had 2 failures, both the test's own: a locator matched the decision in the stage detail and in the receipt alike. Scoped to the Sign-off details, the rerun gave 4 passed. The run view's tests still pass (6 of 6).
- **By hand,** on the demo build at 1440×900: a question asked in `c-0143`, followed to its run view, then to Review and decide at the gate, released there with `approve`; the run view showed it released with its receipt, and the chat showed the same receipt.

**Every check:** the results are added below once run on this branch.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets, which this change doesn't touch.

## Decisions

- The sign-off page is the run view's own route with an optional segment, not a second page that copies it.
- The panel is the chat's `SignOffPanel`, unchanged; its words about "the conversation" stay true, since the released answer shows there too.

## Docs updated

- [Frontend](../../../architecture/frontend.md): WP-UI-02, part 1 in the §12 template, and the build order.
- [Web screens](../../../architecture/web-screens.md): what the sign-off page has built so far.
- [State](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

The repository has no issues for these; each belongs to a later work package of [web screens](../../../architecture/web-screens.md#build-order).

- Return with a reason is part 2.
- The panel doesn't show the classification or the risk tier: the run record doesn't carry them yet.
- The M2 states (maker-checker, two-person, authority) are WP-UI-10.
- A typed address to a sign-off page reloads the app, and the fake forgets runs asked since (as before); the stored runs survive.
