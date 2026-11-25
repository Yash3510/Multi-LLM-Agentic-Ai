---
title: "apps/web: the sign-in browser test on Windows"
type: log
status: implemented
owner: R3
updated: 2026-11-25
date: 2026-11-25
branch: fix/WP-UI-06-sign-in-test-on-windows
pr: 7
work_package: WP-UI-06
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: the sign-in browser test on Windows

## What changed

- `e2e/sign-in.spec.ts` loads the app once in a `beforeAll` hook, waiting for the sign-in page's button, before its two tests run. No assertion changed, and no assertion's time limit changed.

## Why

CI's Windows job had failed since 2026-11-21 on the first assertion of the [sign-in browser test](../../../architecture/frontend.md#wp-ui-06-part-1-sign-in-session-and-sign-out-against-the-server): after `page.goto('/')` the page was still on `http://localhost:4311/` when the 5 s for `toHaveURL(/\/auth$/)` ran out. The cause is timing in the test, not a Windows fault in the app:

- **The same code passed on Windows once.** Trunk at `322f075` ran both sign-in tests on Windows and passed (10 passed). The next run, at `10e51b3`, changed only `ci.yml` (the MinIO job) and failed. The runs at `754620b`, `10e51b3` and `81545b5`, and PR #6, all fail at the same line with the same message.
- **Only the first page of a freshly started dev server fails.** The test is the first to use the dev server on port 4311, which compiles the app's modules the first time a browser asks for them (about 400 modules; a local trace of the test made 1,205 requests). The second test, on the same server a moment later, passes on Windows every time.
- **The Windows runner is several times slower.** The same Python tests take 250 to 285 s there against 33.8 s on the Mac used here, and the first page's redirect takes 0.8 s here, so 5 s is not enough there.

No CI change is needed.

## Files

| Path | Change |
| --- | --- |
| `apps/web/e2e/sign-in.spec.ts` | the `beforeAll` hook that loads the app once |
| `docs/architecture/frontend.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, in the worktree used for WP-UI-05, on this branch (cut from `origin/4ce-core` at `81545b5`).

**The failure, reproduced first.** A temporary dev-only Vite plugin (not committed) delayed each module's first compile by 300 ms, the way a slow machine's first page is slow:

- Before the hook, `SLOW_FIRST_LOAD=300 npx playwright test e2e/sign-in.spec.ts --project=server --reporter=list`: 1 failed, 1 passed. The failure is the Windows one: `Expected pattern: /\/auth$/`, `Received string: "http://localhost:4311/"`, `Timeout: 5000ms`, at `sign-in.spec.ts:22`; the locked-account test passed.
- With the hook, the same command: 2 passed (the first test in 2.7 s, as on a warm server).
- Without the plugin, `npx playwright test e2e/sign-in.spec.ts --project=server --reporter=list`: 2 passed (1.5 s and 0.9 s); and the locked-account test alone (`--grep locked`): 1 passed, so the hook also covers it when it runs first.

**Every check:** the results are added below once run on this branch.

**Not run:** `just secrets` (gitleaks isn't installed here). Windows itself: CI's Windows job on this pull request is the first run there.

## Decisions

- A warm-up hook rather than a longer timeout on the first assertion: the assertions keep Playwright's default limits, and the hook's wait is bounded by its own timeout (the test timeout, 30 s), so a server that never comes up still fails, as a hook timeout.
- None of the CI configuration changes (the frontend owner's instruction of 2026-11-25).

## Docs updated

- [Frontend](../../../architecture/frontend.md): the sign-in browser tests load the app once first, and why.
- [State](../../../state.md): Windows was red from 2026-11-21, and why.
- This entry and the [log index](../../README.md).

## Known limits and follow-ups

The repository has no issues for these.

- The fix is proven on Windows only by CI's run on this pull request. If the dev server's first page ever took longer than 30 s there, the hook would time out and say so.
