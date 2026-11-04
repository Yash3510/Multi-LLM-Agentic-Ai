---
title: Web data contract
type: architecture
status: planned
owner: R3
updated: 2026-11-04
covers:
  - apps/web/src/lib/data/
tags: [4ce, architecture, frontend]
---

# Web data contract

What the web app needs from the 4CE backend, as the screens read it. The screens import only `$lib/data` (`apps/web/src/lib/data/`). Today that module returns a **fake source** that replays a scripted answer in the browser, with no network calls. The backend plugs in by implementing the same `DataSource` interface in that one module, without changing a screen. The types in [`types.ts`](../../apps/web/src/lib/data/types.ts) are the source of truth; this page explains them.

## Interface

| Call | Returns | Used by |
| --- | --- | --- |
| `listChats()` | `ChatSummary[]`, newest first: id, title, updated time and the last run's outcome | the sidebar's chat list and its run markers |
| `getChat(id)` | `Chat` with its `messages`, or `undefined` | the conversation screen (`/c/[id]`) |
| `ask(chatId, question, signal?)` | an async stream of `StreamEvent`s, ending at the sign-off request (or `done`, `stopped`, `error`) | the composer and the live answer |
| `decide(chatId, outcome, by, signal?)` | the rest of the run: `decision`, `receipt`, `done` | the sign-off panel |

The `AbortSignal` stops a stream. The person's Stop button and leaving the chat both abort.

## Messages

A `Message` is a user message or a response. A response carries its run's `events` and `finished`. Everything the answer shows (the stage rail, the status line, tools, sources, sign-off and receipt) is derived from the events, so a reloaded chat looks the same as a live one. A direct reply (no agent chain) carries `direct`: its status line, the model and the time.

## Stream events

Events arrive in order. `at` is the server's time in milliseconds.

| `type` | Carries | Shown as |
| --- | --- | --- |
| `status` | `stage` (one of the six roles, or `replan`), `description`, optional `done` | the stage rail and the live status line |
| `delta` | a piece of the answer's markdown | the answer text, streamed |
| `tool` | a `ToolCall`: id, name, input, output, state (`running`, `done`, `failed`); a repeated id updates the call | the tool-call row |
| `source` | a `Source`: citation number, title, passage | the `[n]` citations and the sources list |
| `sign-off` | the checks for the person to review, each with a verdict | the sign-off panel |
| `decision` | `released` or `withheld`, and who decided | the Sign-off node and the panel's result |
| `receipt` | fingerprint, model, seconds, source count, who signed, external calls observed, and `folds` (titled markdown: full provenance and each agent's own output) | the receipt labels, then the folds; the execution timeline fold is built from the status events |
| `done`, `stopped`, `error` | error: the server's `message` and optional plain-language `advice` | the end of the run; an error shows the run error card, which reads the cause from those two fields |

## The six roles

`planner`, `reader`, `analyst`, `author`, `challenger` and `sign-off`. The stage rail draws Planner, Analyst, Author, Challenger and Sign-off, as the running app does; Reader's work shows in the status line and its tool calls. The rail's states are derived by `deriveRun` in [`stages.ts`](../../apps/web/src/lib/data/stages.ts), following the running app's rules:
- A stage's segment opens at its first status event and closes at the next stage's event, a `done` status, or the end of the run.
- `replan` counts a re-plan: Analyst, Author and Challenger then run again.
- A Challenger description containing "fail" or "pass" sets its verdict.
- `done` after the Sign-off stage with no decision means released.

## Planned

The 4CE API client, server-sent or WebSocket transport, reconnection with resume from the last event, and paging through the chat list are all planned. None is built.
