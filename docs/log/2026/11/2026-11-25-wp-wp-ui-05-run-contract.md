---
title: "apps/web: runs with ids and numbered events in the fake source"
type: log
status: implemented
owner: R3
updated: 2026-11-25
date: 2026-11-25
branch: wp/WP-UI-05-run-contract
pr: 6
work_package: WP-UI-05
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: runs with ids and numbered events in the fake source

## What changed

- **Runs in the fake source:** a run has an id and keeps its events in order, each numbered by `seq` from 1 (`Run`, `RunEvent`). `ask(chatId, question)` starts one and returns its id; `getRun`, `followRun(id, after, signal?)`, `cancelRun` and `decide(runId, outcome)` complete the contract ([WP-UI-05, part 1](../../../architecture/frontend.md#wp-ui-05-part-1-runs-in-the-fake-source-followed-from-the-last-event)). A run plays on whether anyone follows it, so another screen can read the same run.
- **Resuming:** `watchRun` (`src/lib/data/runs.ts`) follows a run to its end and, when a follow ends early (a dropped connection), waits a second and follows again after the last event it saw.
- **The fake's scripted runs:** the full chain to sign-off, a Challenger FAIL and a replan, an error at the Analyst, and a new run whose connection drops once just after the Analyst starts. The stored chats' runs are `run-demo` and `run-0142`.
- **The chat follows its run:** Stop cancels the run, leaving the chat only stops following, and the decision goes through `decide(runId, outcome)` on the follow already open. The decision is recorded as the signed-in person's; the chat no longer passes a name.
- **Sign-off on the rail:** the rail's last node and the audit record's decision row read Sign-off, the plan's name for the sixth role, instead of You.

## Why

The plan's run screens (run view, sign-off page, receipt, audit sheet) all read one run by its id and must look the same after a reload or a dropped connection (ADR-0035 §3). Until now a run existed only as events inside a chat message, with no id, numbering or resume. The server has no run endpoints yet, so the contract is built against the fake source first ([ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md), amended). The frontend owner decided on 2026-11-25 that the sixth role reads Sign-off.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts` | `Run`, `RunEvent` and `Message.runId`; the run calls in `DataSource` |
| `apps/web/src/lib/data/runs.ts` | new: `watchRun`, `ends`, `sleep` |
| `apps/web/src/lib/data/fake.ts` | the run store and its player, the run calls, the dropping run; the stored runs numbered, with ids |
| `apps/web/src/lib/data/fake.test.ts`, `runs.test.ts` | the run tests, in place of the three streaming tests |
| `apps/web/src/routes/c/[id]/+page.svelte` | the chat follows its run; Stop cancels it |
| `apps/web/e2e/chat.spec.ts` | new: a dropped connection resumes and approve releases |
| `apps/web/src/lib/ui/components/StageRail.svelte`, `ResponseMessage.svelte`, `rail.test.ts`, `audit.test.ts` | Sign-off in place of You |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/adr/0046-connect-screens-to-the-server-one-at-a-time.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, uv 0.12.17, Python 3.12.14, in a fresh worktree after `uv sync --all-packages --locked` and `npm --prefix apps/web ci`. `just`, `pre-commit` and gitleaks aren't installed on this machine, so each `just check` recipe's commands were run directly, as the justfile writes them, and every commit message went through `tools/repo_check.py --commit-msg` and `tools/commit_words.py` by hand.

**Tests first:**

- `npx vitest run src/lib/data/fake.test.ts src/lib/data/runs.test.ts` before the code: 7 failed in `fake.test.ts` (`source.followRun is not a function`, `source.cancelRun is not a function`), and `runs.test.ts` failed to load (`Failed to resolve import "./runs"`). After it: `npx vitest run src/lib/data/` 5 files, 75 tests passed.
- Two edge cases found in review, tests first: following from `after` -1 waited at the sign-off until the 5 s test timeout, and following an unknown run resolved `[]` instead of rejecting, which would leave a watcher trying it every second (`npx vitest run src/lib/data/fake.test.ts`: 2 failed, 48 passed). After the fix: `npx vitest run src/lib/data/` 5 files, 75 tests passed.
- `npx vitest run src/lib/ui/components/rail.test.ts` before the label change: 1 failed (expected `SIGN-OFF`, received `YOU`), 6 passed. After it, with `audit.test.ts`: 9 passed.
- `npx playwright test e2e/chat.spec.ts --project=desktop --project=tablet`: 2 passed (13.9 s and 14.0 s). This browser test guards the chat; on the old code the same question just ran to sign-off, so it is not a failing-first test. `runs.test.ts` is.

**Every check,** on the final code (after the two edge-case fixes):

| Recipe | Commands | Result |
| --- | --- | --- |
| `lint` | `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright` | 227 files already formatted; all checks passed; 0 errors, 0 warnings |
| `imports` | `uv run lint-imports` | 14 contracts kept, 0 broken |
| `repo-check`, `neutrality` | `uv run python tools/repo_check.py`, `tools/neutrality_check.py` | exit 0, nothing reported |
| `docs` | `uv run python tools/docs_check.py`, then with `--base origin/4ce-core` once this entry was committed | exit 0 both times |
| `licences` | `tools/sbom.py`, `licence_gate.py build/sbom/python.cdx.json`, `import_scan.py …`, `licence_gate.py --bundle` | 78 components checked; 114 files scanned; 5 bundled services checked |
| `test` | `uv run pytest -m "not postgres and not redis and not minio"` | 807 passed, 97 deselected, 33.8 s |
| `web-lint` | `npm --prefix apps/web run lint`, `run lint:design`, `run check` | ESLint and Prettier clean; design lint clean; svelte-check 1450 files, 0 errors, 0 warnings |
| `web-test` | `npm --prefix apps/web test`, `npm --prefix apps/web exec -- vitest run --root . --dir tools` | 93 files, 568 tests passed; 3 files, 16 tests passed |
| `web-e2e` | `npm --prefix apps/web run e2e` | 12 passed in 27.2 s: desktop and tablet on the demo build (the new chat test 14.2 s on each), and the 2 sign-in tests on the `server` project; 0 `window.fetch` warnings |

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets, which this change doesn't touch; CI, which runs on the pull request.

## Decisions

- [ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md), amended on 2026-11-25 with the frontend owner's approval: WP-UI-05 in two parts; the fake source stays the only stand-in, with no MSW and no new dependency.
- [ADR-0035](../../../adr/0035-frontend-foundations.md) §3 followed: events numbered per run, and resuming after the last sequence seen.
- `decide` takes no name: the source records the signed-in person, as the server will.
- The frontend owner's decisions of 2026-11-25: the sixth role reads Sign-off; sign-off stays in the chat and gets its own page later, both reading one run.

## Docs updated

- [Frontend](../../../architecture/frontend.md): WP-UI-05, part 1 in the §12 template, with the endpoints proposed for WP-RT-01; the build order no longer says MSW.
- [Web data contract](../../../architecture/web-data-contract.md): the run calls, a Runs section, numbered events.
- [Web screens](../../../architecture/web-screens.md): what the conversation has built so far.
- [Design system](../../../architecture/design-system.md): the rail's labels.
- [ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md): the amendment.
- [State](../../../state.md), this entry and the [log index](../../README.md).

## Known limits and follow-ups

The repository has no issues for these; each is a later work package of [web screens](../../../architecture/web-screens.md#build-order).

- The fake keeps runs in memory: a full reload forgets the runs asked since, and a second tab has its own fake. The stored runs survive. Durable runs come with the server (WP-RT-01).
- A question asked in a chat isn't kept with the chat, as before: leaving and coming back shows the stored messages only, though the run itself can still be read by its id. Keeping it comes with the sign-off page (WP-UI-02), where deciding must show in the chat too.
- The chat shows nothing while it reconnects; the status line and the shell's banner come with the run view (WP-UI-01).
