---
title: "apps/web: the run view"
type: log
status: implemented
owner: R3
updated: 2026-11-26
date: 2026-11-26
branch: wp/WP-UI-01-run-view
pr: 8
work_package: WP-UI-01
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: the run view

## What changed

- **The run view at `/runs/[runId]`** ([WP-UI-01, part 1](../../../architecture/frontend.md#wp-ui-01-part-1-the-run-view)). It shows the stage rail and status line, and the open stage's detail below them: its lines with their times, a second try marked, the Analyst's tool calls and sources (the Reader's included), the Author's draft, the Challenger's lines and the checks, and at Sign-off who decided or that it waits. It also has Cancel while live and the run error card, and once released, the chat's receipt and details panel. It reads the run with `getRun` and follows it from its last event, and an unknown run id is not found.
- **The rail's nodes open stages** on the run view: reached nodes are tabs (click or Enter; ←/→, Home and End move between them), the open one tinted. The chat's rail is unchanged.
- **Reconnecting is said out loud:** `watchRun` takes an options object with `onreconnecting`, and the status line reads "Connection lost. Reconnecting…" meanwhile, in the chat and the run view.
- **The chat links each answer to its run view** (View run, beside the status line).
- **A question asked in a chat stays with it:** the fake keeps it and its answer, `getChat` fills the answer in from its run, and the chat opened again follows a live answer after its last event.
- **`stageDetails`** in `stages.ts` works out what each rail stage did.
- **`AnswerBody`**: the answer's prose and its styles move out of `ResponseMessage` unchanged, so the draft looks as an answer does.
- **The receipt's Audit button** shows only where there is an audit record to open (the chat).

## Why

The plan's build order puts the run view next ([web screens](../../../architecture/web-screens.md#build-order)): one run in full, read by its id, the same run the chat shows (ADR-0035 §3). Keeping asked questions with the chat was planned for the sign-off step. It came forward because the new View run link would otherwise lead away from a live answer that the chat then forgot. The status line's reconnect wording closes the gap the last entry left: the chat showed nothing while it reconnected.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/routes/runs/[runId]/+page.ts`, `+page.svelte` | new: the run view |
| `apps/web/src/lib/data/stages.ts`, `stages.test.ts` | `stageDetails` |
| `apps/web/src/lib/data/runs.ts`, `runs.test.ts` | `watchRun`'s options and `onreconnecting` |
| `apps/web/src/lib/data/fake.ts`, `fake.test.ts` | a question asked stays with its chat; `getChat` fills answers in from their runs |
| `apps/web/src/lib/ui/components/StageRail.svelte`, `rail.test.ts` | the nodes as tabs on the run view, the open one tinted |
| `apps/web/src/lib/ui/components/StatusLine.svelte`, `status-line.test.ts` | the reconnect line and the View run link |
| `apps/web/src/lib/ui/components/AnswerBody.svelte`, `ResponseMessage.svelte` | the answer's prose in its own component; the run id and reconnect state passed to the status line |
| `apps/web/src/lib/ui/components/ReceiptStrip.svelte`, `signoff.test.ts` | Audit only with a handler |
| `apps/web/src/routes/c/[id]/+page.svelte` | the chat follows a live answer when opened again and passes the run link and reconnect state |
| `apps/web/e2e/run-view.spec.ts` | new: the run view in the browser |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, in the worktree used since WP-UI-05, on this branch (stacked on `wp/WP-UI-05-run-contract` at `019cad1`).

**Tests first** (each failed before its change, then passed):

- `npx vitest run src/lib/data/stages.test.ts`: 2 failed (`stageDetails is not a function`), then 9 passed.
- `npx vitest run src/lib/data/runs.test.ts`: 2 failed (`signal?.addEventListener is not a function`: the options object reached the old signature), then `npx vitest run src/lib/data/` 5 files, 78 tests passed.
- `npx vitest run src/lib/ui/components/status-line.test.ts`: the reconnect line 1 failed, then 5 passed; the View run link 1 failed, then 6 passed.
- `npx vitest run src/lib/ui/components/rail.test.ts`: 3 failed (no tabs), then 10 passed.
- `npx vitest run src/lib/data/fake.test.ts -t "keeps a question"`: 1 failed, then `src/lib/data/` 79 passed.
- Not test-first: the Audit change came first. The receipt test that listed Audit then failed; it now passes a handler, and a new test checks there is no Audit without one.
- svelte-check refused a type cast in the first `stageDetails` commit; the record is now built without it (its own commit).

**In the browser:**

- `npx playwright test e2e/run-view.spec.ts --project=desktop --project=tablet`: the first run had 2 failures, both the test's own timing: it checked the chat while the page swap was still under way. The test now waits for the chat's composer, and the rerun gave 6 passed in 15.0 s. These tests cover the new route and link, so they were not run against the code before them.
- By hand, on the demo build at 1440×900: the stored run's tabs by pointer and keyboard; then a question asked in `c-0143`, followed to its run view live and on to sign-off, back to the chat (answer and review panel still there), approved, and its run view released with the receipt.

**Every check:** the results are added below once run on this branch.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets, which this change doesn't touch.

## Decisions

- [ADR-0035](../../../adr/0035-frontend-foundations.md) §3 followed: the run view reads the run by id and follows it after the last `seq`.
- Keeping asked questions with the chat moved from WP-UI-02 into this change, because the run view's link needs it.
- The rail's nodes follow the tabs pattern on the run view (manual activation, as web-screens.md gives the keys); the chat's rail keeps its buttons.
- No audit record on the run view yet: the Audit button waits for the audit sheet (WP-UI-03) rather than opening a second copy of the chat's dialog.

## Docs updated

- [Frontend](../../../architecture/frontend.md): WP-UI-01, part 1 in the §12 template, and the build order.
- [Web data contract](../../../architecture/web-data-contract.md): asked questions kept with the chat, `watchRun`'s options, `stageDetails`.
- [Web screens](../../../architecture/web-screens.md): what the run view and the chat have built so far.
- [Design system](../../../architecture/design-system.md): the rail's tabs on the run view, the status line's reconnect line and link, `AnswerBody`, the Audit button.
- [State](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

The repository has no issues for these; each belongs to a later work package of [web screens](../../../architecture/web-screens.md#build-order).

- At sign-off the run view sends the person to the conversation to decide: the sign-off page and Return with a reason are WP-UI-02.
- The run view's receipt has no Audit button until the audit sheet (WP-UI-03).
- The routing table, budgets spent, "could not check", and links to evidence review and the assessment wait for the run record to carry them.
- The shell's connection banner waits for the one shared connection (the rest of WP-UI-05); the status line says it per run meanwhile.
- The Author's draft joins every try's text. Today's fake streams one draft, so it reads right; a run that drafts twice would show both until the record marks the draft.
- The fake keeps runs and asked questions in memory: a full reload forgets them, as before.
- The Windows CI job stays red on these branches until PR 7 lands (the sign-in browser test).
- The change is about 1,300 lines against the ~400 guideline. About 330 of them are the answer's prose moved unchanged, and about a third are tests and docs.
