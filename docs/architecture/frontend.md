---
title: Frontend
type: architecture
status: planned
owner: R3
updated: 2026-11-27
covers:
  - apps/web/
tags: [4ce, architecture, frontend]
---

# Frontend

Everything needed to build `apps/web`, the 4CE web UI and Pack Studio, independently of the backend work. **Pranay, the frontend owner, develops it.** The backend stream builds the server and the database on `4ce-core` at the same time. The two meet at one contract: the server's OpenAPI document.

The web UI is not built yet; the backend contract below is. This page is the starting point and the working agreement.

## What is already decided

| Record                                                         | Decides                                                                                                                                                                                                                                        | Status                                                                             |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [ADR-0035](../adr/0035-frontend-foundations.md)                | Stack and exact versions, static serving from the server, live updates, the fake API until the backend lands, roles and labels, devices, languages, theme, accessibility, no glass, icons, quality gates, clean room                           | proposed; accepted by the frontend owner; R1 to accept §2 (serving) and §5 (roles) |
| [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) | How the licence gate treats MPL-2.0 build and test tools (lightningcss, axe-core) and permissive licences Appendix A doesn't name                                                                                                              | proposed; R4 to accept before `apps/web` lands on `4ce-core`                       |
| [ADR-0041](../adr/0041-exact-match-look.md)                    | The look matches the running 4CE app, measured; its amendment sets premium base components (the running app's Phosphor icons, hairline depth, soft focus glow). Supersedes ADR-0035's theme, colour values, no-glass rule and design-lint part | proposed; accepted by the frontend owner; R1 to accept                             |
| [Design system](design-system.md)                              | Tokens, type, spacing, depth, motion, states, numbers, keyboard, tables, print, icons                                                                                                                                                          | planned                                                                            |

Frontend work can proceed against these now. The parts R1 and R4 decide take effect when `apps/web` is merged into `4ce-core`.

A polish pass on `wp/WP-F-10-polish` departs from the exact-match finish on purpose: softer, rounder corners through new radius tokens, full-pill buttons and search fields, and a flat finish with no added depth ([log](../log/2026/11/2026-11-11-wp-wp-f-10-polish.md)).

## Where the code goes

The layout is fixed by the [repository rules](repository.md#layout):

```
apps/web/
├── package.json, package-lock.json   npm, versions pinned exactly (ADR-0035 §1)
├── README.md
├── src/
│   ├── routes/                pages only: load data, compose components
│   └── lib/
│       ├── ui/                the design system: tokens and base components
│       ├── components/<area>/ feature components (chat/, signoff/, studio/ …)
│       ├── stores/            client state
│       ├── api/               typed API client, generated at build, never committed
│       └── i18n/              UI strings per locale
├── static/                    self-hosted fonts, icons, images
└── tests/
```

- **Naming:** Svelte components PascalCase (`SignOffPanel.svelte`), TypeScript modules camelCase (`trustView.ts`), folders kebab-case.
- **No industry words.** The [neutrality check](repository.md#checks) covers `apps/` too: labels such as "Asset" or "Application" come from the active pack's vocabulary, never from the code.
- **No upstream code.** Components the team wrote in the earlier fork are rebuilt from their behaviour on the new tokens, not copied (ADR-0035 §14).

## The backend contract

**Status: built (slice 1).** `GET /api/openapi.json` is the source of truth, and the types are generated from it with openapi-typescript at build time.

**One origin.** The UI and the API are served from the same host; every API path starts with `/api`. In development, the Vite dev server proxies `/api` to the backend, so the browser still sees one origin.

**The contract is [api.md](api.md).** In short: sign in with `POST /api/auth/signin`; the browser keeps an HttpOnly `fource_token` cookie; send the `fource_csrf` cookie's value as `X-CSRF-Token` on every POST, PUT, PATCH or DELETE; errors are `{"error": {"code", "message"}}`.

### User roles and agent roles are different lists

- **User roles** (who a person is): Admin, Author, Reviewer, Viewer, Auditor, Pack Author, Pack Approver. They come back in `roles` and decide what a person may do.
- **Agent roles** (who did a step of a run): Planner, Reader, Analyst, Author, Challenger, Sign-off (ADR-0035 §5). They label the stage rail.

## Running the backend locally

Sign-in, the session and sign-out come from the server in a dev build, so `npm run dev` needs it running:

```
just setup                                     # once: Python, packages, git hooks, a .env with fresh secrets
just dev                                       # the server on http://127.0.0.1:8000, SQLite, no Docker needed
just create-user you@example.com --role Admin  # once: asks for a password
just web-dev                                   # the web app on http://localhost:5173, /api sent to the server
```

`npm run dev` sends `/api` to `http://127.0.0.1:8000`; set `API_TARGET` to use another server. `VITE_4CE_DEMO=1 npm run dev` runs the fully fake app with no server. To test against PostgreSQL instead, run `just services` and set `FOURCE_DATABASE_URL` in `.env` as `.env.example` shows.

## What to build, in order

1. **The screen inventory** (ADR-0035's follow-up): every screen the pitch demo and Phase 1 need, which becomes the frontend's work packages.
2. **WP-F-09:** design tokens, base components and the app shell, with the `/ui` route that shows every component in every state (ADR-0035 §13).
3. **Sign-in, session and sign-out** against slice 1: the first screens with a real backend ([WP-UI-06, part 1](#wp-ui-06-part-1-sign-in-session-and-sign-out-against-the-server)).
4. **Runs in the fake source:** ids, numbered events and following from the last event, so every run screen reads one run ([WP-UI-05, part 1](#wp-ui-05-part-1-runs-in-the-fake-source-followed-from-the-last-event)).
5. **WP-UI-01:** chat, cases and the run view with the stage rail ([part 1, the run view](#wp-ui-01-part-1-the-run-view)). Runs, cases and live events come in later backend slices; until then, the fake source ([web data contract](web-data-contract.md)). Propose each endpoint's shape in a PR to this page, so the backend builds what the screens need.
6. **WP-UI-02** sign-off panel ([part 1, the sign-off page](#wp-ui-02-part-1-the-sign-off-page)), **WP-UI-03** receipt and provenance ([part 1, the full receipt](#wp-ui-03-part-1-the-full-receipt); [part 2, file cards](#wp-ui-03-part-2-deliverables-as-file-cards); [part 3, the audit sheet](#wp-ui-03-part-3-the-audit-sheet)), **WP-UI-04** Sovereignty page.

### WP-UI-06, part 1: sign-in, session and sign-out against the server

**Built** ([log](../log/2026/11/2026-11-17-wp-wp-ui-06-sign-in.md)). The first part of [WP-UI-06](web-screens.md#proposed-work-packages), in the master plan's §12 template. The rest of WP-UI-06 (session expiry with the return path, no-access and error pages) needs WP-ID-02 and WP-UI-05, and is written up when it starts.

**Goal:** a person signs in against a real 4CE server, stays signed in across reloads until the token expires, and signs out. Every other screen stays on its stand-in data.

**Interface:**

- `src/lib/data/server.ts`: `serverSession()`, the `DataSource` calls `currentUser`, `signIn`, `signOut`, `setupStatus`, `signUp` and `createFirstAccount` over `fetch`, and `ServerError` (`code`, `status`, `message`).
- `chooseSource` (`src/lib/data/source.ts`): a demo build (`VITE_4CE_DEMO=1`) stays fake throughout; a dev build takes those calls from the server and everything else from the fake replay; a production build is still refused.
- `npm run dev` proxies `/api` to `API_TARGET`, by default `http://127.0.0.1:8000` (`just dev`).

**Inputs and outputs:**

- `signIn(email, password)` sends `POST /api/auth/signin` and answers the person: `name` is `display_name` (the email when that is empty), and `role` is `admin` for the Admin role, `user` otherwise.
- `currentUser()` sends `GET /api/auth/session`: the person on 200, `undefined` on 401 or when no 4CE answer comes back.
- `signOut()` sends `POST /api/auth/signout` with `X-CSRF-Token` set to the `fource_csrf` cookie's current value. 204 and 401 both mean signed out.
- An error answer, `{"error": {"code", "message"}}`, becomes a `ServerError` that carries the server's message. Anything else (no answer, or a status without that envelope, such as the dev proxy's 500 while the server is down) becomes `unreachable`: "Can't reach the 4CE server. Check that it's running, then try again."
- `setupStatus()` answers `{ firstAccount: false }`; `signUp` and `createFirstAccount` refuse, because accounts are made with `fource-server create-user`.
- When sign-out fails, the shell shows the message as an error toast and stays where it is.

**Acceptance tests:**

- Vitest, with `fetch` stubbed (`server.test.ts`, `source.test.ts`):
  1. sign-in posts the email and password as JSON and maps the answer; the password is in no answer, storage or URL;
  2. for `invalid_credentials` (401), `account_locked` (423), `rate_limited` (429) and `rate_limit_unavailable` (503) the error is the server's message, with its code and status;
  3. a rejected `fetch` and a 500 without the envelope are `unreachable`;
  4. the session is the person on 200, and `undefined` on 401 or `unreachable`; it asks with a load function's own `fetch` when given one;
  5. sign-out sends the CSRF cookie's value; 204 and 401 resolve; `csrf_failed` and `unreachable` reject;
  6. `chooseSource`: demo is fake throughout, dev signs in through the server and keeps the fake rest, production is refused.
- Playwright (`e2e/sign-in.spec.ts`), through the dev server against `fource-server`, started with `uv run fource-server migrate` and `serve` on a throwaway SQLite database:
  7. a wrong password shows the server's message, keeps the email and clears the password;
  8. the right password opens the app, a reload stays signed in, and signing out returns to sign-in, where a reload stays;
  9. five wrong passwords lock the account, and the sixth attempt says when to try again.

**Ledger:** nothing new; the server already records every sign-in, failure, lockout and sign-out.

**Files:** `src/lib/data/` (`server.ts`, `source.ts` and their tests), `src/lib/ui/components/AppShell.svelte`, `vite.config.ts`, `playwright.config.ts`, `e2e/` and the README, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), an ADR for connecting screens one at a time, `state.md` and a work-log entry.

**Neutrality:** no sector terms.

**Out of scope:** the generated client (WP-UI-05); the rest of WP-UI-06; roles other than Admin (WP-ID-02); sign-up and the first account, which the server doesn't offer; the server serving the built UI.

**Depends on:** WP-ID-01 and the sign-in rate limit (WP-F-07), both built. No new dependency.

**Reviewer:** R3.

**Size:** one pull request.

### WP-UI-05, part 1: runs in the fake source, followed from the last event

**Built, in draft PR 6** ([log](../log/2026/11/2026-11-25-wp-wp-ui-05-run-contract.md)). The first part of [WP-UI-05](web-screens.md#proposed-work-packages), in the master plan's §12 template. The generated client and the live-event transport wait for the server's run endpoints (WP-RT-01). Until then the fake source is the stand-in, with no MSW ([ADR-0046](../adr/0046-connect-screens-to-the-server-one-at-a-time.md)).

**Goal:** a run has an id and numbered events. A screen can read it as it stands and follow it from the last event it saw, so the chat, the run view, the sign-off page, the receipt and the audit sheet all show the same run (ADR-0035 §3).

**Interface:**

- `src/lib/data/types.ts`: `Run` (id, chat, question, events, finished) and `RunEvent`, a `StreamEvent` with its `seq`, counted from 1 in each run. A response `Message` carries its `runId`.
- `DataSource`: `ask(chatId, question)` starts a run and returns its id; `getRun(id)`; `followRun(id, after, signal?)`; `cancelRun(id)`; `decide(runId, outcome)`.
- `src/lib/data/runs.ts`: `watchRun(source, id, after, signal?)` follows a run to its end and, when the connection drops, follows again after the last event it saw.
- Proposed endpoints for WP-RT-01: `POST /api/chats/{chat_id}/runs` with the question, answering the run's id; `GET /api/runs/{run_id}`; `POST /api/runs/{run_id}/cancel`; `POST /api/runs/{run_id}/decision` with the outcome; and the run's events on the one WebSocket as `{run, seq, ...}`, from a given `after`.

**Inputs and outputs:**

- `followRun` yields the events after `after`, then each new one as it happens, and ends when the run ends (`done`, `stopped` or `error`) or the signal aborts. It stays open while the run waits for sign-off. It rejects for a run that doesn't exist, and a negative `after` starts at the first event.
- A follow can end before the run does: the connection dropped. Following again after the last `seq` seen gives the rest, with no gap and no repeat.
- `cancelRun` ends a live run with `stopped`. Aborting a follow only stops listening; the run carries on.
- `decide` records the decision as the signed-in person's, so a screen never names who decided. Followers then get `decision`, `receipt` and `done`.
- The fake's scripted runs play at real pace: the full chain to sign-off; a Challenger FAIL and a replan (a question about rounding); an error at the Analyst (a question about the server being down); a connection that drops once at the Analyst (a question about the connection dropping). The stored chats' runs are `run-demo` and `run-0142`.
- The chat (`/c/[id]`) follows its run: Stop cancels it, leaving the chat stops following, and a dropped connection resumes after a second.

**Acceptance tests:**

- Vitest (`fake.test.ts`, `runs.test.ts`):
  1. a run streams through the chain in time order to sign-off, its events numbered 1, 2, 3 and on, with no gap;
  2. after `decide`, a follower gets `decision`, `receipt` and `done` with the signed-in person's name, and `getRun` shows the run finished;
  3. following after `seq` n gives exactly the events after n;
  4. `cancelRun` ends a live run with `stopped`, and nothing comes after it;
  5. aborting a follow stops it, and the run carries on to sign-off;
  6. the dropping run's first follow ends early, and `watchRun` carries on after the last event, with no gap and no repeat, to the end;
  7. the stored chats' runs are found by id, finished, with their messages' events.
- Playwright (`e2e/chat.spec.ts`, on the demo build): a question whose connection drops still reaches sign-off, and typing `approve` releases it with a receipt.

**Ledger:** nothing new; the fake writes no ledger entries.

**Files:** `src/lib/data/` (`types.ts`, `fake.ts`, `runs.ts` and their tests), `src/routes/c/[id]/+page.svelte` and `e2e/chat.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), an amendment to ADR-0046, `state.md` and a work-log entry.

**Neutrality:** no sector terms.

**Out of scope:** the generated client and the WebSocket (the rest of WP-UI-05, after WP-RT-01); the run view and every other new screen (WP-UI-01 onwards); MSW; any new dependency.

**Depends on:** nothing built yet on the server; WP-RT-01 for the server side.

**Reviewer:** R3.

**Size:** one pull request.

### WP-UI-01, part 1: the run view

**Built, in draft PR 8** ([log](../log/2026/11/2026-11-26-wp-wp-ui-01-run-view.md)), stacked on WP-UI-05, part 1. The run view part of [WP-UI-01](web-screens.md#proposed-work-packages), in the master plan's §12 template; cases are part 2. It runs on the fake source until the server serves runs (WP-RT-01).

**Goal:** one run in full at `/runs/[runId]`: where it is, what each stage did, what was checked, and its receipt once released. It reads the same run the chat follows, by id, and follows it from the last event it has, through a dropped connection (ADR-0035 §3).

**Interface:**

- `src/routes/runs/[runId]/`: `+page.ts` loads the run with `getRun`; an unknown id is a 404.
- `stageDetails(events)` in `src/lib/data/stages.ts`: what each rail stage did. That is its status lines, with the time since the run started and the try they belong to; the tool calls and sources found while it worked (the Reader's inside the Analyst's, as on the rail); and the text it drafted.
- `watchRun(source, id, after, { signal, retryMs, onreconnecting })`: the signal and the retry wait move into an options object, which also tells the screen when a dropped connection starts and stops reconnecting.
- `StageRail`: given `onselect`, its nodes become tabs that open a stage's detail, for any reached node, live or finished. ←/→, Home and End move between them, and Enter opens one. `onshown` reports where the rail's light rests. Without these (the chat) nothing changes.
- `StatusLine`: `reconnecting` reads "Connection lost. Reconnecting…" on a live run; `href` adds a link to the run view.
- `ReceiptStrip` shows its Audit button only when given `onaudit`: the run view's audit sheet comes with WP-UI-03.
- `AnswerBody`: the answer's prose and its styles, moved out of `ResponseMessage` unchanged, so the run view shows the Author's draft as the chat shows an answer.
- The fake keeps a question asked in a chat with it, and `getChat` gives each answer as far as its run has got. The chat opened again follows a live answer after its last event, so leaving it for the run view loses nothing (planned for WP-UI-02, brought forward because the run view's link needs it).
- No new endpoint. The run view reads `GET /api/runs/{run_id}` and the run's events, and cancels with `POST /api/runs/{run_id}/cancel`, as proposed in [WP-UI-05, part 1](#wp-ui-05-part-1-runs-in-the-fake-source-followed-from-the-last-event).

**Inputs and outputs:**

- A live run shows the rail with the working node, the status line, a Cancel button and the selected stage's detail. The detail follows the rail's light, which trails a live run one hop at a time, until the person picks a stage. A finished run shows the rail as it ended; a released one adds the receipt, what was checked and the details panel, as in the chat.
- A stage's detail shows its lines, with a second try marked as one; the Analyst's tool calls and sources (the Reader's included); the Author's draft; the Challenger's lines and the checks with their verdicts; and at Sign-off, who decided and when, or that it is waiting. A node not reached opens nothing.
- Cancel ends the run `stopped`, in the run view and in the chat.
- A dropped connection: the status line says "Connection lost. Reconnecting…" until the follow resumes, in the run view and in the chat. No event is missed or repeated.
- Each answer in the chat that has a run links to its run view, and the chat opened again shows the question asked there and follows its answer on.
- A run that stopped with an error shows the run error card, without a retry: retrying belongs to the chat.

**Acceptance tests:**

- Vitest:
  1. `stageDetails`: the normal run gives the Planner its line, the Analyst the Reader's search with its tool call and both sources, the Author the answer's text and the Challenger its two lines. The replanned run marks the second try's Analyst, Author and Challenger lines as try 2, and gives the Challenger the replan line;
  2. `watchRun` calls `onreconnecting(true)` when a follow ends early and `onreconnecting(false)` when it follows again, once each for the dropping run, and never for a run whose connection holds;
  3. `StageRail` with `onselect` draws tabs, the selected one `aria-selected`; a click selects; ←/→ move across the reached nodes and Enter selects; a node not reached is disabled; `onshown` reports where the light rests, trailing a live run;
  4. `StatusLine` with `reconnecting` replaces the live line and announces it; with `runId` it links to the run view;
  5. the fake keeps a question asked in a chat with it, its answer as far as the run has got, and another source keeps its own chats;
  6. `ReceiptStrip` without `onaudit` has no Audit button.
- Playwright (`e2e/run-view.spec.ts`, on the demo build):
  7. the stored run `run-0142` shows the rail released and the receipt; the Analyst's tab shows the search and the sources; → then Enter opens the Author's draft;
  8. a question asked in the chat links to its run view, which follows the run live; Cancel stops it, and the chat opened again shows it stopped;
  9. an unknown run id is not found.

**Ledger:** nothing new; the fake writes no ledger entries.

**Files:** `src/routes/runs/[runId]/`, `src/lib/data/` (`stages.ts`, `runs.ts`, `fake.ts` and their tests), `src/lib/ui/components/` (`StageRail.svelte`, `StatusLine.svelte`, `AnswerBody.svelte`, `ResponseMessage.svelte`, `ReceiptStrip.svelte` and their tests), `src/routes/c/[id]/+page.svelte` and `e2e/run-view.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Neutrality:** no sector terms; fixture values stay neutral.

**Out of scope:**

- the sign-off page and Return with a reason (WP-UI-02);
- the full receipt, file cards, the audit sheet and the classification banner (WP-UI-03);
- the assessment and evidence review (WP-UI-08, WP-UI-07);
- cases (part 2);
- the routing table, budgets spent and "could not check", which the run record doesn't carry yet;
- the shell's connection banner, which waits for the one shared connection (the rest of WP-UI-05).

**Depends on:** WP-UI-05, part 1 (draft PR 6).

**Reviewer:** R3.

**Size:** one pull request.

### WP-UI-02, part 1: the sign-off page

**Built, in draft PR 9** ([log](../log/2026/11/2026-11-26-wp-wp-ui-02-sign-off-page.md)), stacked on WP-UI-01, part 1. The first part of [WP-UI-02](web-screens.md#proposed-work-packages), in the master plan's §12 template; Return with a reason is part 2. The frontend owner decided on 2026-11-25 that sign-off stays in the chat and gets this page too, both reading one run.

**Goal:** a named person decides at `/runs/[runId]/sign-off` whether a run's work is released. The page is the run view with the sign-off panel docked, on the same run as the chat, so a decision taken in either shows in both.

**Interface:**

- `/runs/[runId]/sign-off` is its own route, whose page renders the run view's page with `signOff` set, so both addresses are one page on one run and only the second docks the panel. (An optional route segment would do the same in one folder, but the repository's folder rule allows plain `[param]` folders only.)
- The panel is the chat's `SignOffPanel`, open only while the run waits at the gate. `decide(runId, outcome)` records the decision. If the source refuses it, because someone decided first, the page says nothing was released.
- While the run waits, the run view's Sign-off stage links to this page.
- No new endpoint: the decision is `POST /api/runs/{run_id}/decision`, as proposed in [WP-UI-05, part 1](#wp-ui-05-part-1-runs-in-the-fake-source-followed-from-the-last-event).

**Inputs and outputs:**

- At the gate the panel shows the draft, the checks, the sources and the typed-word release, as in the chat. `approve` releases and Withhold withholds; the run then goes on to its decision, receipt and end on the page, and the chat shows the same.
- Before the gate the page is the live run view, with a line saying the panel opens at the gate. After the decision it is the decided run view with its receipt.
- A decision the source refuses: "Nothing was released:" and the reason, and the run view stays as the source has it.

**Acceptance tests:**

- Vitest: nothing new; the page is made of components that already have tests.
- Playwright (`e2e/sign-off.spec.ts`, on the demo build): a question asked in the chat, opened at its sign-off page, waits for the gate, then `approve` releases it there and the chat shows it released; a decided run's sign-off page has no panel.

**Ledger:** nothing new; the fake writes no ledger entries.

**Files:** `src/routes/runs/[runId]/` (the run view, with the docked panel), `src/routes/runs/[runId]/sign-off/` and `e2e/sign-off.spec.ts`, all under `apps/web/`.

**Docs:** this page, [web screens](web-screens.md), `state.md` and a work-log entry.

**Neutrality:** no sector terms.

**Out of scope:** Return with a reason (part 2); the receipt in full and the audit sheet (WP-UI-03); the maker-checker, two-person and authority states (WP-UI-10); the classification and risk tier in the panel, which the run record doesn't carry yet.

**Depends on:** WP-UI-01, part 1 (draft PR 8).

**Reviewer:** R3.

**Size:** one pull request, under ~400 changed lines.

### WP-UI-02, part 2: Return with a reason

**Built, in draft PR 10** ([log](../log/2026/11/2026-11-26-wp-wp-ui-02-return-with-reason.md)), stacked on part 1. web-screens.md gives the sign-off panel a Return that sends the work back with a reason; the frontend owner asked for it in the chat's panel too (2026-11-25).

**Goal:** the person at the gate can return the work with a reason instead of releasing it, from the sign-off page or the chat, and the reason stays with the run.

**Interface:**

- `decide(runId, outcome, reason?)`: a reason goes with `withheld` and makes it a return; a blank reason is refused. The `decision` event carries the `reason`.
- `SignOffPanel`: Return opens a reason field in place of the typed word, with Cancel; Return it is enabled only once a reason is written. Withhold stays, for keeping the work back without a reason.
- The rail's Sign-off node notes `returned`, with the withheld dash, which is the design system's returned glyph. The run view's Sign-off stage says who returned it, when and why, and the chat shows the reason under the answer.
- No new endpoint: the reason goes in `POST /api/runs/{run_id}/decision` with the outcome.

**Inputs and outputs:**

- Return, a reason, Return it: the run is decided withheld with that reason, nothing is released, and it ends without a receipt, as a withheld run does.
- Cancel, or Escape in the reason field, goes back to the typed word with nothing decided.

**Acceptance tests:**

- Vitest:
  1. the fake records the reason with a return and refuses a blank one;
  2. `deriveRun` notes `returned` for a withheld decision with a reason, and `withheld` without one;
  3. the panel's Return asks for a reason, sends it with `withheld`, stays disabled while the reason is blank, and Cancel goes back.
- Playwright (`e2e/return.spec.ts`, on the demo build): a run returned from the chat's panel shows the reason under the answer and in its run view's Sign-off stage.

**Ledger:** nothing new; the fake writes no ledger entries. The server records the decision with its reason (WP-LG-01, `approval.decision`).

**Files:** `src/lib/data/` (`types.ts`, `fake.ts`, `stages.ts` and their tests), `src/lib/ui/components/` (`SignOffPanel.svelte`, `ResponseMessage.svelte`, `signoff.test.ts`), `src/routes/c/[id]/+page.svelte`, `src/routes/runs/[runId]/+page.svelte` and `e2e/return.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Neutrality:** no sector terms.

**Out of scope:** a returned run going back to the agents for another try; for now a return ends the run, and asking again is a new question. Also out of scope: the receipt in full and the audit sheet (WP-UI-03).

**Depends on:** WP-UI-02, part 1 (draft PR 9).

**Reviewer:** R3.

**Size:** one pull request, under ~400 changed lines.

### WP-UI-03, part 1: the full receipt

**Built, in draft PR 11** ([log](../log/2026/11/2026-11-26-wp-wp-ui-03-receipt.md)), stacked on WP-UI-02, part 2. The first part of [WP-UI-03](web-screens.md#proposed-work-packages); deliverables as file cards are part 2, and the audit sheet part 3.

**Goal:** a released run's receipt gives the whole sealed record, where people already look: the details panel under the answer in the chat and at the end of the run view.

**Interface:**

- `Receipt` gains the record's other facts: the `classification` in the pack's words, the `pack` (name, version and hash), the `routing` table (each role's model), the `skills` used with their version hashes, and the `ledger` position.
- `DetailsPanel` gains a Receipt tab, last, given the `receipt` and the `decision`. It shows the fingerprint short with Show all and Copy, who decided and when with the time zone, the classification, pack, models, skills ("None used" when none), external connections, ledger entry and working time. A run with no receipt has no tab, and the record never changes after release.
- The working time is the run's own: the fake sets `seconds` from the run's stages, so the receipt and the status line agree. The fake's record is neutral: classification Internal, pack Core 1.0.0, no skills, ledger entry 1042.
- No new endpoint: these come with the run's `receipt` event.

**Acceptance tests:**

- Vitest: the fake's receipt carries the record and the run's working time; the Receipt tab shows the short fingerprint, the whole one on Show all, who decided, the pack, the models and the ledger entry.
- Playwright (`e2e/run-view.spec.ts`): the stored run's Receipt tab, in the run view and the chat, gives the pack, the ledger entry and the whole fingerprint.

**Ledger:** nothing new; the fake writes no ledger entries.

**Files:** `src/lib/data/` (`types.ts`, `fake.ts` and its test), `src/lib/ui/components/` (`DetailsPanel.svelte`, `ReceiptStrip.svelte`, `ResponseMessage.svelte`, `signoff.test.ts`), `src/routes/runs/[runId]/+page.svelte` and `e2e/run-view.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Neutrality:** no sector terms; the pack and classification are neutral stand-ins.

**Out of scope:** deliverables as file cards (part 2); the audit sheet (part 3); the QR code and evidence-pack export (M2); the compact sovereignty view beyond the egress count (WP-UI-04).

**Depends on:** WP-UI-02, part 2 (draft PR 10).

**Reviewer:** R3.

**Size:** one pull request, under ~400 changed lines.

### WP-UI-03, part 2: deliverables as file cards

**Built, in draft PR 12** ([log](../log/2026/11/2026-11-27-wp-wp-ui-03-file-cards.md)), stacked on part 1. The file card web-screens.md defines, used first for a released run's deliverables.

**Goal:** the documents a released run produced show as file cards under its receipt, in the chat and at the end of the run view.

**Interface:**

- `FileInfo` in `types.ts`: a file's name, kind (`docx`, `xlsx`, `pptx`…), size in bytes, SHA-256, classification and state (`uploading`, `scanning`, `parsing`, `ready`, `failed`). `Receipt.deliverables` lists the run's files.
- `FileCard`: the kind's Phosphor file icon and a neutral type tag, the name, the size (as the knowledge pages write it), the hash prefix and the classification; a file not yet ready says its state. `ReceiptStrip` shows the deliverables' cards, so both pages get them.
- No new endpoint: the files come with the run's `receipt` event. Opening or downloading one waits for files from the server.

**Acceptance tests:**

- Vitest: the fake's receipt lists a ready `docx`; `FileCard` shows the tag, name, size, hash prefix and classification, and the state of a file not yet ready.
- Playwright (`e2e/run-view.spec.ts`): the stored run's deliverable card shows in the run view and the chat.

**Ledger:** nothing new. **Neutrality:** no sector terms; the file name uses the fixtures' neutral case id.

**Files:** `src/lib/data/` (`types.ts`, `fake.ts`, `fake.test.ts`), `src/lib/ui/components/` (`FileCard.svelte` and its test, `ReceiptStrip.svelte`) and `e2e/run-view.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Out of scope:** opening and downloading files, upload progress, and attachments in the composer (WP-UI-09); revision cards per deliverable version; the audit sheet (part 3).

**Depends on:** WP-UI-03, part 1 (draft PR 11). **Reviewer:** R3. **Size:** one pull request, under ~400 changed lines.

### WP-UI-03, part 3: the audit sheet

**Built, in draft PR 13** ([log](../log/2026/11/2026-11-27-wp-wp-ui-03-audit-sheet.md)), stacked on part 2. The audit sheet web-screens.md defines at `/runs/[runId]/audit`, following the design system's print rules.

**Goal:** a decided run as a printed A4 record, from the run view's Audit button, so paper and screen agree.

**Interface:**

- `src/routes/runs/[runId]/audit/`: `+page.ts` loads the run (an unknown id is a 404); `+page.svelte` is the sheet. On screen it is a print preview with one Print button; in print only the sheet shows, black on white with 1 px rules.
- The sheet: the header (the 4CE mark, the classification banner and "Audit sheet"), the question, the static rail, the approval block (who, when with the time zone, the fingerprint in groups of four), the review shown (the released text and each check's verdict with the sources it cites), the record (pack with its hash in groups of four, models, external connections, ledger entry) and the footer (printed when and by whom, and the ledger entry). A run not yet decided says so and links to its run view.
- Hashes print whole in groups of four with the format module's `formatHashFull` (and short with `formatHashShort`). The Receipt tab now uses them too, and gives the pack hash Show all and Copy like the fingerprint.
- The run view's receipt gets its Audit button back, opening the sheet; the chat's still opens its audit record.

**Acceptance tests:**

- Vitest: the Receipt tab shows the fingerprint and the pack hash whole, in groups of four, on their Show all buttons.
- Playwright (`e2e/audit.spec.ts`): the stored run's audit sheet, opened from its run view, has the banner, the approver, the grouped fingerprint and the checks, and one Print button; a run not yet decided says so.

**Ledger:** nothing new; printing writes no entry yet. **Neutrality:** no sector terms.

**Files:** `src/routes/runs/[runId]/audit/`, `src/routes/runs/[runId]/+page.svelte`, `src/lib/ui/components/DetailsPanel.svelte` and `signoff.test.ts`, and `e2e/audit.spec.ts` and `e2e/run-view.spec.ts`, all under `apps/web/`.

**Docs:** this page, [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Out of scope:** the QR code in the footer (M2, after the QR step is approved); the organisation's own mark (the 4CE mark stands in); the chat's audit record dialog, which stays as it is.

**Depends on:** WP-UI-03, part 2 (draft PR 12). **Reviewer:** R3. **Size:** one pull request, under ~400 changed lines.

### WP-UI-07, part 1: evidence review

**Built, in draft PR 14** ([log](../log/2026/11/2026-11-27-wp-wp-ui-07-evidence-review.md)), stacked on WP-UI-03, part 3. The first part of [WP-UI-07](web-screens.md#proposed-work-packages). Step 3 of the plan goes in six pull requests: evidence review in four parts (part 2: pages, zoom and pan; part 3: Verify; part 4: Correct), then the assessment in two (WP-UI-08).

**Goal:** check what the Reader read from a piece of evidence against the page itself, at `/evidence/[evidenceId]`.

**Interface:**

- `Evidence` and `Observation` in `types.ts`: an evidence item's name, the `<Document kind>` it was read as, its pages (image and size), the reader's model, and its observations. Each observation has a number in reading order, its page, a box as fractions of the page, a label, a value and unit, and a confidence. `getEvidence(id)` gives one, and a `Source` can name the `evidenceId` it was read from.
- The evidence viewer: the page image with numbered boxes, and the observation list in step with them. Selecting a box selects its row and the reverse. An observation read with less than full confidence shows the dashed `observation-unsure` glyph and "check". `?box=` opens with that box selected.
- The run view's Analyst stage links each source that has evidence to its review.
- Proposed endpoint for the backend: `GET /api/evidence/{evidence_id}`.

**Acceptance tests:**

- Vitest: the fake gives the stored run's evidence with its observations; the viewer keeps box and row selection in step, and marks an unsure observation.
- Playwright (`e2e/evidence.spec.ts`): from the stored run's Analyst stage to the evidence review; `?box=` opens with its box selected.

**Ledger:** nothing new. **Neutrality:** no sector terms; the page and its values use the fixtures' neutral case, rule and units.

**Files:** `src/lib/data/` (`types.ts`, `fake.ts`, `fake.test.ts`), `src/lib/ui/components/EvidenceViewer.svelte` and its test, `src/routes/evidence/[evidenceId]/`, `src/routes/runs/[runId]/+page.svelte` and `e2e/evidence.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Out of scope:** zoom and pan, page navigation (part 2); Verify and Correct (parts 3 and 4); the Reader's live reading; capture on tablets.

**Depends on:** WP-UI-03, part 3 (draft PR 13). **Reviewer:** R3. **Size:** one pull request, 533 changed lines, accepted in review.

### WP-UI-07, part 2: pages, zoom and pan

**In progress** on `wp/WP-UI-07-pages-and-zoom`, stacked on WP-UI-07, part 1. The rest of evidence review goes in three pull requests, each planned under about 400 changed lines: this one, then Verify (part 3), then Correct (part 4).

**Goal:** move between a piece of evidence's pages and read one closely, at `/evidence/[evidenceId]`.

**Interface:**

- Page navigation: Previous page and Next page around "Page n of m", when the evidence has more than one page. The list shows that page's observations, so boxes and rows stay in step.
- `?page=` opens a page. `?box=` opens its box's page, with the box selected.
- Zoom, from 100 % (the page fits) to 400 %, with Zoom out and Zoom in by pointer or keyboard. The point at the centre stays there.
- Pan when zoomed: the page scrolls in its frame, by wheel, trackpad, touch or scrollbar, and by keyboard with the arrow keys once the page or a box has focus. The page is a region named for its page and zoom ("Page 2 of 2, zoom 200%"). With nothing focusable in it, current Chrome and Firefox let it take focus, so a page with nothing read still pans there; Safari doesn't.
- The fake's stored run reads a second page.

**Acceptance tests:**

- Vitest: the fake's evidence has two pages; the viewer moves between pages with the list following, opens on the page asked for or the page of `?box=`, zooms from 100 % to 400 % and back, and names the page as a region for its page and zoom.
- Playwright (`e2e/evidence.spec.ts`): `?page=2` opens the second page and `?box=4` the page its box is on; zoomed in by keyboard, the arrow keys pan the page.

**Ledger:** nothing new. **Neutrality:** no sector terms; the second page uses the fixtures' neutral case and units.

**Files:** `src/lib/data/fake.ts` and `fake.test.ts`, `src/lib/ui/components/EvidenceViewer.svelte` and its test, `src/routes/evidence/[evidenceId]/` and `e2e/evidence.spec.ts`, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), [web screens](web-screens.md), the [design system](design-system.md), `state.md` and a work-log entry.

**Out of scope:** Verify and Correct (parts 3 and 4); zoom by wheel or pinch beyond the browser's own; dragging the page to pan with a mouse; keeping the address in step with the page shown.

**Depends on:** WP-UI-07, part 1 (draft PR 14). **Reviewer:** R3. **Size:** one pull request, planned at about 340 changed lines.

## When `apps/web` lands on `4ce-core`

The first PR that adds `apps/web` also wires it into the repository's checks. In the same PR:

- [ ] **Node 24 LTS** (ADR-0035 §1) in the README's setup and in CI. The README is done (2026-11-04). CI is not: `ci.yml` must add a Node 24 step and a Playwright browser install before `just check` passes there, and that change is for a human.
- [x] **just recipes** for installing (`npm ci`), format, lint and types (prettier, eslint, svelte-check), unit tests (vitest) and browser tests (Playwright), all inside `just check`: `web-install`, `web-format`, `web-lint` (which also runs the design lint), `web-test` (which also runs the icon-generator and design-lint tests), `web-e2e` and `web-dev`. `just setup` runs `npm ci` (2026-11-04).
- [x] **The repo check learns the frontend's naming:** PascalCase components and their `.test.ts` files, SvelteKit's route files, the web app's formatter config and message project, and colocated or `e2e/` tests are accepted by `tools/repo_check.py`, with tests (2026-11-04). Modules stay kebab-case, so there is no camelCase rule.
- [ ] **The licence gate reads the npm SBOM:** generate it with `@cyclonedx/cyclonedx-npm` into `build/sbom/` and pass it to `tools/licence_gate.py`, which already checks any CycloneDX SBOM. ADR-0036 must be decided first.
- [ ] **Dependabot** gains the npm ecosystem, targeting `4ce-core`.
- [ ] **`.gitignore`** gains `apps/web/src/lib/api/` (generated).
- [ ] **The server serves the built UI** (ADR-0035 §2: every path that isn't `/api` returns the fallback page). This is a backend change in `apps/server`; ask the backend stream.
- [ ] **This page** moves from `planned` to `active`, and describes what was built.

## How to work alongside the backend stream

- **Start each session with `just sync`.** Work on a branch named `wp/<WP-id>-<short-title>` off `4ce-core`, never on `4ce-core` itself.
- **Small Conventional Commits** (`feat(web): add the sign-in screen`), `just check` green, then a pull request into `4ce-core` with one work-log entry (`just new-doc log <branch-name>`).
- **Contract changes go through this page.** If a screen needs an endpoint or a field, propose it here first; the backend stream builds to it.
- **Everything else** about working in the repository is in [CONTRIBUTING](../../CONTRIBUTING.md) and the [repository rules](repository.md).
