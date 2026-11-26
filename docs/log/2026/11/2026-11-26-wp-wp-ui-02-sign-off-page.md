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
- **One page, one run:** `/runs/[runId]/sign-off` is its own route, whose page renders the run view's page with `signOff` set. Both addresses show the same run, so a decision taken there or in the chat shows in both.
- **Refusals:** a decision the source refuses (someone decided first) shows "Nothing was released" with the reason.
- **The link:** while the run waits, the run view's Sign-off stage offers Review and decide.

## Why

The plan gives sign-off its own page, the run view with the panel docked (web-screens.md, `/runs/[runId]/sign-off`), and the frontend owner decided on 2026-11-25 to keep the chat's panel as well, both on one run. The owner asked for step 2 in pull requests under ~400 changed lines each. Reusing the run view's page, rather than extracting it into a component, keeps this one small. Extracting it would count every moved line.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/routes/runs/[runId]/+page.svelte`, `+page.ts` | the docked panel, the refusal, the Review and decide link; `signOff` in the page data |
| `apps/web/src/routes/runs/[runId]/sign-off/+page.svelte`, `+page.ts` | new: the sign-off route, rendering the run view's page with `signOff` |
| `apps/web/e2e/sign-off.spec.ts` | new: the sign-off page in the browser |
| `docs/architecture/frontend.md`, `web-screens.md`, `docs/state.md`, `docs/log/README.md` | the docs below |

## How it was verified

On macOS (arm64), Node 24.21.0, in the worktree used since WP-UI-05, on this branch (stacked on `wp/WP-UI-01-run-view` at `b707080`).

- **The first shape failed the repository check.** The page was first one route with an optional segment (`[[panel=panel]]`, a matcher in `src/params/panel.ts`, test-first). `uv run python tools/repo_check.py` refused the folder: "folder '[[panel=panel]]' is not kebab-case". The rule allows plain `[param]` folders only, as approved on 2026-11-04. So the sign-off page became its own route rendering the run view's page, and the matcher and its test went. The repository check then exited 0, and the browser tests below were run again.
- **In the browser:** `npx playwright test e2e/sign-off.spec.ts --project=desktop --project=tablet`. The first run had 2 failures, both the test's own: a locator matched the decision in the stage detail and in the receipt alike. Scoped to the Sign-off details, the rerun gave 4 passed. On the final route, `e2e/sign-off.spec.ts` with `e2e/run-view.spec.ts` gave 10 passed.
- **Review fix, test first:** the line for a run not yet at the gate also showed between the decision and the end of the run, a flash after Approve (in the fake the decision comes about 300 ms before `done`). The sign-off browser test now watches the page while releasing. Before the fix it failed (`sawGateLine` expected false, received true); with the line shown only until the review request arrives, `npx playwright test e2e/sign-off.spec.ts --project=desktop --project=tablet` gave 4 passed.
- **By hand,** on the demo build at 1440×900: a question asked in `c-0143`, followed to its run view, then to Review and decide at the gate, released there with `approve`; the run view showed it released with its receipt, and the chat showed the same receipt.

**Every check,** each `just check` recipe's commands run directly (`just` isn't installed here), on the final code:

| Recipe | Commands | Result |
| --- | --- | --- |
| `lint` | `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright` | 229 files already formatted; all checks passed; 0 errors, 0 warnings |
| `imports` | `uv run lint-imports` | 14 contracts kept, 0 broken |
| `repo-check`, `neutrality` | `uv run python tools/repo_check.py`, `tools/neutrality_check.py` | exit 0, nothing reported (the first shape's run: exit 1, quoted above) |
| `docs` | `uv run python tools/docs_check.py`, and with `--base wp/WP-UI-01-run-view` | exit 0 both times |
| `licences` | `tools/sbom.py`, `licence_gate.py build/sbom/python.cdx.json`, `import_scan.py …`, `licence_gate.py --bundle` | 78 components checked; 114 files scanned; 5 bundled services checked |
| `test` | `uv run pytest -m "not postgres and not redis and not minio"` | 807 passed, 97 deselected, 36.6 s |
| `web-lint` | `npm --prefix apps/web run lint`, `run lint:design`, `run check` | ESLint and Prettier clean; design lint clean; svelte-check 1461 files, 0 errors, 0 warnings |
| `web-test` | `npm --prefix apps/web test`, `npm --prefix apps/web exec -- vitest run --root . --dir tools` | 93 files, 579 tests passed; 3 files, 16 tests passed |
| `web-e2e` | `npm --prefix apps/web run e2e` | 22 passed in 47.0 s: desktop and tablet on the demo build (the sign-off page's 2 tests and the run view's 3 among them), and the 2 sign-in tests on the `server` project; 0 `window.fetch` warnings |

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets, which this change doesn't touch.

## Decisions

- The sign-off page renders the run view's page rather than copying it or moving it into a component. An optional route segment would be tidier, but the repository's folder rule doesn't allow one; widening that rule is the owner's call.
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
- The panel's "Drafted on" names `qwen/qwen3-8b`, written into the chat and the run view, until a run carries its model.
- The receipt's working time is the fake's fixed 9.4 s, while the status line sums the stages (12.2 s on the same run); the full receipt (WP-UI-03) is where they should agree.
