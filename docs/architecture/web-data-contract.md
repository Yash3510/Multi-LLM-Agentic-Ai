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

## Session

| Call | Returns | Used by |
| --- | --- | --- |
| `currentUser()` | the signed-in `User` (id, name, email, role `admin`, `user` or `pending`), or `undefined` | every screen, to decide between the app and the sign-in page |
| `signIn(email, password)` | the `User`; rejects with a plain message when the email or password is wrong | the sign-in page |
| `signUp(name, email, password)` | the new `User`; `pending` when an admin must approve new accounts | the sign-up form |
| `signOut()` | nothing; the session ends on the server too | the user menu |
| `setupStatus()` | `{ firstAccount }`: true when the server has no account yet | the sign-in page, to show "get started" instead of sign in |
| `createFirstAccount(name, email, password)` | the first `User`, always `admin` | the first-run form |

**Passwords.** A password goes from the form straight to the backend call. The web app never logs it, stores it (memory, `localStorage`, `sessionStorage`, cookies), puts it in a URL or query string, or sends it anywhere else. The session itself is the backend's: an HTTP-only cookie is expected, so the web app never holds a token.

**The fake source refuses production.** The fake replay accepts any email and drops the password unread. A production build that would run on it refuses to start (`src/lib/data/source.ts`, tested in `source.test.ts`), unless it was built as a demo with `VITE_4CE_DEMO=1`. The Playwright tests build that way.

## Workspace

| Call | Returns | Used by |
| --- | --- | --- |
| `workspaceCounts()` | how many models, knowledge bases, prompts, skills and tools the person can see | the workspace tabs |
| `listModels()` | `WorkspaceModel[]`: id, name, base model, description, updated time, owner, and whether it is enabled, hidden and writable by the person | the workspace Models list |
| `listBaseModels()` | `WorkspaceItem[]` (id, name): the models a custom model can build on | the model editor's Base Model picker |
| `listKnowledge()` | `KnowledgeBase[]`: id, name, description, updated time, owner, file count (when known), whether the person may change it, and its source (`local`, or `connected` with provider, source name and auth mode) | the Knowledge list and the model editor's Knowledge picker |
| `createKnowledge(name, description)` | creates a private knowledge base and returns it | the create-knowledge dialog |
| `deleteKnowledge(id)` | deletes a knowledge base | the Knowledge list's row menu |
| `listTools()` | `WorkspaceItem[]`: the tools the person can see | the model editor's Tools picker |
| `listSkills()` | `WorkspaceItem[]`: the active skills | the model editor's Skills picker |
| `saveModel(record)` | creates a custom model from `ModelRecord` (id, name, base, params, meta; empty values left out) and returns it as a `WorkspaceModel`; rejects with a message naming the id when it is taken | the model editor's Save & Create |

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
| `sign-off` | the checks for the person to review, each with a verdict and the citation numbers it rests on (`cites`), and on a later try a `revision` (try number, objections, removed and added lines) | the sign-off panel and its changes view; the receipt's revision card |
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
