---
title: "Connect screens to the server one at a time"
type: adr
status: planned
owner: R3
updated: 2026-11-25
covers: []
tags: [4ce, adr]
number: 46
decision_status: proposed
superseded_by: null
---

# ADR-0046: Connect screens to the server one at a time

## Context

Every screen in `apps/web` reads one `DataSource` ([web data contract](../architecture/web-data-contract.md)). Until now only the fake replay implemented it, and a production build refuses to run on it. The server now serves sign-in, the session and sign-out ([api](../architecture/api.md)); chat, documents and settings are not built yet. [ADR-0035](0035-frontend-foundations.md) §4 plans types generated from the OpenAPI document and MSW fixtures in the meantime, but neither is in the app yet: that is WP-UI-05. The frontend owner wants the app connected to the backend piece by piece while the backend is built, sign-in first ([WP-UI-06, part 1](../architecture/frontend.md#wp-ui-06-part-1-sign-in-session-and-sign-out-against-the-server)).

## Decision

1. **One `DataSource`, call by call.** A dev build's source is the fake replay with the calls the server serves laid over it (`{ ...createFakeSource(), ...serverSession() }` in `src/lib/data/source.ts`). Each backend slice moves its calls over the same way, until nothing is left on the fake.
2. **Three builds.** A demo build (`VITE_4CE_DEMO=1`) stays fake throughout and needs no server. A dev build uses the server for what it serves and stand-in data for the rest. A production build still refuses to start until every screen is on the server, because it must never put stand-in data in front of people.
3. **One origin in development.** `npm run dev` proxies `/api` to the server (`API_TARGET`, by default `http://127.0.0.1:8000`), so the cookies and the CSRF header work as they will when the server serves the UI (ADR-0035 §2).
4. **Errors.** The server's `message` is shown for every error envelope. A reply without the envelope did not come from 4CE (no answer, or a proxy's own error page), so it reads "Can't reach the 4CE server".
5. **Hand-written shapes until WP-UI-05.** The request and answer shapes of the connected calls are written by hand in `src/lib/data/server.ts`, and a browser test against a real server checks them. This departs from ADR-0035 §4 until WP-UI-05 generates the types; no dependency is added.
6. **Browser tests against a real server.** Screens on the server are tested on the dev server, in front of a throwaway `fource-server` started the repo's own way (`uv run fource-server migrate`, then `serve`) on a fresh SQLite database with a random secret. The other browser tests keep running on the demo build.

## Alternatives considered

| Option | Why not |
| --- | --- |
| MSW fixtures for every call first, then a switch per screen | MSW isn't in the app yet (WP-UI-05), and fixtures don't exercise the real cookies, CSRF check and errors |
| Generate the client now (openapi-typescript, openapi-fetch) | A new dependency, and a web build that needs the server's OpenAPI document, for three calls; WP-UI-05 does it for every call |
| Let a production build run on the mix | It would show stand-in data to real people |
| Test sign-in on a production build | The only production build allowed today is the demo build, which is fake throughout |

## Consequences

- `npm run dev` needs the server running (`just dev`, and `just create-user` once). `VITE_4CE_DEMO=1 npm run dev` gives the fully fake app.
- `npm run e2e` (and so `just check`) now needs the Python environment from `just setup`; CI already has it.
- Stand-in screens still name the stand-in account where they show an owner.
- When the last call moves, `chooseSource` loses the fake and production builds start working.

## Amendment: WP-UI-05 in two parts (2026-11-25)

The run screens (run view, sign-off page, receipt, audit sheet) need runs that a screen can find by id and follow from the last event, and the server has no run endpoints yet.

1. **Part 1 now, in the fake source.** Runs get ids and numbered events, with `getRun`, `followRun` (the events after a given `seq`), `cancelRun`, and `watchRun` to resume after a dropped connection ([web data contract](../architecture/web-data-contract.md#runs)). The screens are built against these calls.
2. **Part 2 with the server.** The generated client and the WebSocket wait for the run endpoints (WP-RT-01). The run calls then move over like the session calls did, as a `serverRuns()` laid over the fake in `source.ts`, with no screen changed.
3. **No MSW and no new dependency.** The fake source stays the only stand-in until each call is on the server.

The frontend owner approved this amendment on 2026-11-25.

## Status

Proposed on 2026-11-17; amended on 2026-11-25. To be accepted by the frontend owner (R3), and by R1 for the departure from ADR-0035 §4.
