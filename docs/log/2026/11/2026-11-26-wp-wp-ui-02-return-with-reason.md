---
title: "apps/web: Return with a reason"
type: log
status: implemented
owner: R3
updated: 2026-11-26
date: 2026-11-26
branch: wp/WP-UI-02-return-with-reason
pr: 10
work_package: WP-UI-02
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: Return with a reason

## What changed

- **Return in the sign-off panel** ([WP-UI-02, part 2](../../../architecture/frontend.md#wp-ui-02-part-2-return-with-a-reason)), on the sign-off page and in the chat. Return swaps the typed word for a focused reason field. Return it sends the work back once a reason is written, and Cancel or Escape goes back with nothing decided. Withhold stays.
- **The reason travels with the decision:** `decide(runId, outcome, reason?)`, where a reason with `withheld` is a return; the fake refuses a blank one and puts the `reason` on the `decision` event.
- **The reason is shown:** the rail's Sign-off node notes `returned`, and the run view's Sign-off stage says who returned it, when and why. A line under the chat's answer gives the reason too.
- **Known limits from review of #8** recorded in the data contract: answer text joins every try's deltas, sources are listed once per stage, and a refused cancel isn't handled.

## Why

web-screens.md gives the sign-off panel a Return that sends the work back with a reason, and the frontend owner asked for it in the chat's panel too (2026-11-25). Step 2 goes in pull requests under ~400 changed lines; this is the second.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts`, `fake.ts`, `stages.ts` and `fake.test.ts`, `stages.test.ts` | the reason on `decide` and the `decision` event; the `returned` note |
| `apps/web/src/lib/ui/components/SignOffPanel.svelte`, `signoff.test.ts` | Return, the reason field, Cancel and Return it |
| `apps/web/src/lib/ui/components/ResponseMessage.svelte` | the reason under a returned answer |
| `apps/web/src/routes/c/[id]/+page.svelte`, `apps/web/src/routes/runs/[runId]/+page.svelte` | the reason passed to `decide`; the run view's Sign-off stage says it |
| `apps/web/e2e/return.spec.ts` | new: Return in the browser |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, in the worktree used since WP-UI-05, on this branch (stacked on `wp/WP-UI-02-sign-off-page` at `b5c92d3`).

**Tests first** (each failed before its change, then passed):

- `npx vitest run src/lib/data/fake.test.ts src/lib/data/stages.test.ts`: 2 failed (no reason on the decision; no `returned` note), then `src/lib/data/` 81 passed.
- `npx vitest run src/lib/ui/components/signoff.test.ts`: 1 failed (no Return), then 10 passed.

**In the browser:** `npx playwright test e2e/return.spec.ts --project=desktop --project=tablet`: 2 passed. A run returned from the chat's panel shows its reason under the answer, and in its run view's Sign-off stage, whose node notes returned.

**Every check,** each `just check` recipe run directly (`just` isn't installed here), on the final code:

| Recipe | Result |
| --- | --- |
| `lint` (`ruff format --check .`, `ruff check .`, `pyright`) | 230 files already formatted (134 Python, 96 Markdown); all checks passed; 0 errors |
| `imports`, `repo-check`, `neutrality` | 14 contracts kept; exit 0, nothing reported |
| `docs` (`docs_check.py`, and `--base wp/WP-UI-02-sign-off-page`) | exit 0 both times |
| `licences` | 78 components checked; 114 files scanned; 5 bundled services checked |
| `test` (`pytest -m "not postgres and not redis and not minio"`) | 807 passed, 97 deselected |
| `web-lint` (`run lint`, `run lint:design`, `run check`) | ESLint and Prettier clean; design lint clean; svelte-check 1462 files, 0 errors |
| `web-test` (`npm test`, tools vitest) | 93 files, 582 tests passed; 3 files, 16 tests passed |
| `web-e2e` (`npm run e2e`) | 24 passed in 48.4 s, the 2 sign-in tests on the `server` project among them |

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets, which this change doesn't touch.

## Decisions

- A return is a `withheld` decision with a reason, not a third outcome. That matches the design system's returned glyph, the withheld dash, and leaves the outcome type and every screen reading it alone.
- Withhold stays beside Return, so keeping the work back without a reason is still one press. Say if Return should replace it.
- A return ends the run; sending the work back to the agents for another try is out of scope.

## Docs updated

- [Frontend](../../../architecture/frontend.md): WP-UI-02, part 2 in the §12 template.
- [Web data contract](../../../architecture/web-data-contract.md): the reason on `decide` and `decision`, and the known limits for runs from the server.
- [Web screens](../../../architecture/web-screens.md): Return on the sign-off page and in the chat.
- [Design system](../../../architecture/design-system.md): Return in the panel and the returned note.
- [State](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

The repository has no issues for these; each belongs to a later work package of [web screens](../../../architecture/web-screens.md#build-order).

- A return ends the run; another try with the reason attached waits for the server's runs.
- The chat still shows a withheld or returned draft in the thread, as it did for Withhold before this change, though the panel says nothing enters the conversation until it is approved.
- The data contract's three known limits for runs from the server (see the contract).
- As in part 1: the panel's "Drafted on" names `qwen/qwen3-8b` until runs carry their model, and the receipt's working time is the fake's fixed 9.4 s.
