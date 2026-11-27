---
title: Web data contract
type: architecture
status: planned
owner: R3
updated: 2026-11-27
covers:
  - apps/web/src/lib/data/
tags: [4ce, architecture, frontend]
---

# Web data contract

What the web app needs from the 4CE backend, as the screens read it. The screens import only `$lib/data` (`apps/web/src/lib/data/`). Today that module returns a **fake source** that replays a scripted answer in the browser, with no network calls, except that a dev build takes sign-in, the session and sign-out from the 4CE server ([ADR-0046](../adr/0046-connect-screens-to-the-server-one-at-a-time.md)). The backend plugs in by implementing the same `DataSource` interface in that one module, call by call, without changing a screen. The types in [`types.ts`](../../apps/web/src/lib/data/types.ts) are the source of truth; this page explains them.

## Interface

| Call | Returns | Used by |
| --- | --- | --- |
| `listChats()` | `ChatSummary[]`, newest first: id, title, updated time and the last run's outcome | the sidebar's chat list and its run markers |
| `getUserSettings()` / `saveUserSettings(change)` | the person's own settings (`UserSettings`: system prompt, advanced parameters left at Default are absent, interface choices by key); saving merges the given parts, and interface choices merge by key | the settings dialog's pages |
| `setStatus(status \| undefined)` | sets or clears the short status shown in the user menu (on `User.status`) | the user menu's status dialog |
| `activeUsers()` | how many people are signed in now | the user menu's active count |
| `listUsers()` / `addUser(person)` / `updateUser(id, change)` / `deleteUser(id)` / `restoreUser(id)` | everyone with an account (`AdminUser`: role, joined and last-active times), the signed-in admin first; passwords given here go only to the backend and are never kept; a delete can be undone in the same session | the admin People list and its dialogs |
| `listGroups()` / `createGroup(draft)` / `updateGroup(id, draft)` / `deleteGroup(id)` / `restoreGroup(id)` / `setGroupMember(group, user, on)` / `userGroups(user)` | groups (`Group`: name, description, who may share to it, stored permissions, member ids); members change at once; a delete can be undone in the same session | the admin Groups tab and group editor |
| `getDefaultPermissions()` / `saveDefaultPermissions(p)` | the permissions everyone with the user role has, as stored; missing keys fall back to built-in defaults (`lib/ui/permissions.ts`); the chat key `tool_settings` maps to the API's per-tool settings permission | the default permissions editor |
| `leaderboard()` / `listFeedback()` / `deleteFeedback(id)` / `restoreFeedback(id)` / `modelActivity(model, days)` | model standings (`LeaderboardEntry`: Elo rating, wins, losses, top tags), feedback records (`Feedback`: result won/draw/lost, detailed rating, reason, comment, tags, prompt and response), and a model's wins and losses per day (0 days = all time); a delete can be undone in the same session | the admin Evaluations pages |
| `listFunctions()` / `getFunction(id)` | server-side functions (`ServerFunction`: type pipe/filter/action/event, version, description, code, enabled, global, owner), read only in this build; saving, enabling and running wait for the 4CE server | the admin Functions pages |
| `previewAccess(id)` | what a person (or group) can reach, by name: groups, models, knowledge, tools | the admin access preview |
| `getAdminSettings(panel)` / `saveAdminSettings(panel, values)` | an admin settings panel's stored values by key, merged on save (unset keys use the panel's defaults in `lib/ui/admin-panels.ts`); logged | the admin settings tabs |
| `exportAdminData(kind)` / `importAdminConfig(config)` | admin exports (config and chats as JSON, users as CSV; the database file only where supported) and a config import that returns the previous config for undo; each logged | the admin Database tab |
| `adminMaintenance(task)` | Documents' Danger Zone: reset uploads, reset vectors (both permanent) or reindex; logged | the admin Documents tab |
| `getAnalytics(days)` | everyone's usage for the admin dashboard (`Analytics`: totals, daily assistant messages, messages by model and by person); 0 days = all time | the admin Analytics tab |
| `listNotes()` / `getNote(id)` / `createNote(draft)` / `updateNote(id, draft)` / `deleteNote(id)` / `restoreNote(id)` / `enhanceNote(content, signal?)` | notes (`Note`: title, Markdown content, owner, read-only flag); a delete can be undone in the same session; Enhance streams a rewrite like an answer | the notes pages |
| `listChannels()` / `getChannel(id)` / `createChannel(draft)` / `deleteChannel(id)` and the `ChannelMessage` calls (`list`, `send`, `edit`, `delete`, `pin`, `react`) / `channelTyping(id)` | channels and their messages (reactions by emoji, replies, pins, edits); channel deletes are logged; typing is simulated presence | the channel pages |
| `playgroundStream(input, signal?)` | the playground's raw model call (a chat turn with system instructions, or a text completion), streamed in pieces | the playground pages |
| `listCalendars()` / `createCalendar(draft)` / `listEvents()` / `saveEvent(event)` / `deleteEvent(id)` / `restoreEvent(id)` | calendars (name, colour) and events (times, all day, repeat, reminder, location, description); a delete can be undone in the same session | the calendar page |
| `listAutomations()` / `getAutomation(id)` / `saveAutomation(draft)` / `deleteAutomation(id)` / `restoreAutomation(id)` / `runAutomation(id)` | scheduled prompts (`Automation`: prompt, model, `Schedule`, destination, active, runs); a delete can be undone in the same session; the fake records runs without calling a model | the automations pages |
| `userChats(id)` | a person's chats for the admin chats view (the fake has chats only for the signed-in person); `updateUser` also takes an avatar choice (default picture or initials) | the admin People list |
| `adminLedger()` | every admin change, newest first (`LedgerEntry`: when, by whom, action, target; never a password) | the admin pages' change trail |
| `getProfile()` / `saveProfile(profile)` | the person's profile (`Profile`: name, bio, gender, birth date, avatar kind, user variables); saving the name renames the signed-in person | the Account page |
| `changePassword(current, next)` | changes the password; both go only to the backend, never logged, stored or put in a URL | the Account page |
| `getUsage()` | the person's usage (`Usage`): totals, a per-day heat map with weekly and running totals, insights, top models and tools; token counts are estimates | the Usage page |
| `exportChats()` / `importChats(chats)` / `archiveAllChats()` / `deleteAllChats()` | every chat with its messages (archived included) for a JSON export; importing adds chats and returns how many; archiving hides them from `listChats()` | the Data Controls page |
| `listArchivedChats()` / `unarchiveChat(id)` / `unarchiveAllChats()` / `deleteChat(id)` | archived chats newest first; unarchiving returns a chat to `listChats()`; deleting removes it for good | the Archived Chats page |
| `listMemories()` / `addMemory(draft)` / `updateMemory(id, draft)` / `deleteMemory(id)` / `clearMemories()` | the person's memories (`Memory`: content, type `user` or `context`, optional path, updated time), most recently changed first | the Personalization page |
| `getChat(id)` | `Chat` with its `messages`, or `undefined`; a response carries its `runId`, and its text, events and `finished` are its run's as far as it has got | the conversation screen (`/c/[id]`) |
| `ask(chatId, question)` | starts a run and returns its id; the question and its answer stay with the chat | the composer |
| `getRun(id)` | the `Run` as it stands (id, chat, question, numbered events, finished), or `undefined` | every run screen; the run view (`/runs/[runId]`) |
| `getEvidence(id)` | an `Evidence`: name, the `<Document kind>` it was read as, its pages (image and size), the reader's model, and its `Observation`s (number in reading order, page, box as fractions of the page, label, value, unit, confidence), or `undefined` | evidence review (`/evidence/[evidenceId]`) |
| `followRun(id, after, signal?)` | the run's events after `after`, then each new one, until the run ends; rejects for a run that doesn't exist; see [Runs](#runs) | the live answer, through `watchRun` |
| `cancelRun(id)` | ends a live run with `stopped` | the composer's Stop; the run view's Cancel |
| `decide(runId, outcome, reason?)` | records the signed-in person's decision on a run waiting for sign-off, which then goes on to `decision`, `receipt` and `done`; a reason with `withheld` returns the work, and a blank reason is refused; rejects for any other run | the sign-off panel, in the chat and on the sign-off page |

The person's Stop button cancels the run. Leaving the chat aborts the follow only: the run carries on.

## Session

| Call | Returns | Used by |
| --- | --- | --- |
| `currentUser(fetch?)` | the signed-in `User` (id, name, email, role `admin`, `user` or `pending`), or `undefined`; a load function passes its own `fetch` | every screen, to decide between the app and the sign-in page |
| `signIn(email, password)` | the `User`; rejects with a message to show as it is (wrong details, a lockout, the rate limit, an unreachable server) | the sign-in page |
| `signUp(name, email, password)` | the new `User`; `pending` when an admin must approve new accounts | the sign-up form |
| `signOut()` | nothing; the session ends on the server too | the user menu |
| `setupStatus()` | `{ firstAccount }`: true when the server has no account yet | the sign-in page, to show "get started" instead of sign in |
| `createFirstAccount(name, email, password)` | the first `User`, always `admin` | the first-run form |

**Passwords.** A password goes from the form straight to the backend call. The web app never logs it, stores it (memory, `localStorage`, `sessionStorage`, cookies), puts it in a URL or query string, or sends it anywhere else. The session itself is the backend's: an HTTP-only cookie is expected, so the web app never holds a token.

**On the server** (`src/lib/data/server.ts`, a dev build): the three session calls go to `/api/auth/signin`, `/session` and `/signout` ([api](api.md)), with the `fource_csrf` cookie's value as `X-CSRF-Token` on sign-out. `name` is the server's `display_name`, or the email when that is empty; `role` is `admin` for the Admin role and `user` for every other. Every refusal rejects with a `ServerError` carrying the server's `code`, `status` and `message`; a reply without the error envelope (no answer, or the dev proxy's own 500 while the server is down) is `unreachable`. A 401 means signed out, for the session and for sign-out alike. `setupStatus()` answers no first account, and `signUp` and `createFirstAccount` refuse: an administrator adds people with `fource-server create-user`.

**Which builds use what.** A demo build (`VITE_4CE_DEMO=1`) is the fake replay throughout, which accepts any email and drops the password unread; the design-reference browser tests build that way. A dev build is the fake replay with the server's session calls. A production build refuses to start (`src/lib/data/source.ts`, tested in `source.test.ts`) until every call is on the server.

## Workspace

| Call | Returns | Used by |
| --- | --- | --- |
| `workspaceCounts()` | how many models, knowledge bases, prompts, skills and tools the person can see | the workspace tabs |
| `listModels()` | `WorkspaceModel[]`: id, name, base model, description, updated time, owner, and whether it is enabled, hidden and writable by the person | the workspace Models list |
| `listBaseModels()` | `WorkspaceItem[]` (id, name): the models a custom model can build on | the model editor's Base Model picker |
| `listKnowledge()` | `KnowledgeBase[]`: id, name, description, updated time, owner, file count (when known), whether the person may change it, and its source (`local`, or `connected` with provider, source name and auth mode) | the Knowledge list and the model editor's Knowledge picker |
| `createKnowledge(name, description)` | creates a private knowledge base and returns it | the create-knowledge dialog |
| `deleteKnowledge(id)` | deletes a knowledge base | the Knowledge list's row menu |
| `getKnowledge(id)` / `updateKnowledge(id, {name, description})` | one knowledge base (undefined when missing); saves its name and description | the knowledge detail header (saved a second after typing stops) |
| `listContents(base, {folder, query, content, sort, direction})` | one folder's `KnowledgeFolder[]` and `KnowledgeDocument[]` (folders first) and the total; `query` matches names, and the extracted text too when `content` is set | the knowledge detail list |
| `getDocumentText(id)` / `saveDocumentText(id, text)` | a document's extracted text, the text retrieval indexes; saving replaces it | the document sheet |
| `addDocument(base, {name, text, size?, folder?})` | adds a document from typed text or an uploaded file's extracted text | Add text content, Upload files |
| `removeDocument(base, id)` | removes a document from this base only; the stored file stays | a document's Delete |
| `createFolder(base, name, parent?)`, `renameItem(base, id, name)`, `deleteFolder(base, id, {contents})` | folders: create inside the open folder, rename a folder or document, delete a folder with its contents or move them up to its parent | the knowledge detail |
| `resetKnowledge(base)` | removes every document and folder from the base | Reset |
| `listPrompts()` / `getPrompt(id)` | `Prompt`: id, name, command (no slash), live text, tags, on/off, updated time, owner, whether the person may change it, and the live version's id | the Prompts list and prompt page |
| `createPrompt({name, command, content, tags})` | creates a prompt whose first version is live | the create-prompt dialog, clone and JSON import |
| `updatePrompt(id, {name, command, tags})`, `setPromptActive(id, active)`, `deletePrompt(id)` | rename, switch on or off, delete | the prompt page and list |
| `listVersions(id)` | `PromptVersion[]` newest first: id, text, commit message, author, time | the prompt page's history |
| `addVersion(id, {content, message?, live})`, `setLiveVersion(id, version)`, `deleteVersion(id, version)` | add a version (live or not), choose the live one, delete one; deleting the live version is refused | the prompt page |
| `listTools()` | `Tool[]`: id, name, description, Python source, version from its header, updated time, owner, whether the person may change it | the Tools list and the model editor's Tools picker |
| `getTool(id)`, `createTool({id, name, description, content})`, `updateTool(id, {name, description, content})`, `deleteTool(id)` | one tool; create (rejects a taken id); change it; delete it. The screen asks the person to accept the risk of running code before creating or importing | the tool editor and Tools list |
| `listSkills()` | `Skill[]`: id, name, description, instructions, on/off, updated time, owner, whether the person may change it; the model editor's picker shows only the switched-on ones | the Skills list and the model editor's Skills picker |
| `getSkill(id)`, `createSkill({id, name, description, instructions})`, `updateSkill(id, {name, description, instructions})`, `setSkillActive(id, active)`, `deleteSkill(id)` | one skill; create (switched on; rejects a taken id); change its text without touching on/off; switch it; delete it | the skill editor and Skills list |
| `saveModel(record)` | creates a custom model from `ModelRecord` (id, name, base, params, meta; empty values left out) and returns it as a `WorkspaceModel`; rejects with a message naming the id when it is taken | the model editor's Save & Create |

## Messages

A `Message` is a user message or a response. A response carries its `runId`, its run's numbered `events` and `finished`. Everything the answer shows (the stage rail, the status line, tools, sources, sign-off and receipt) is derived from the events, so a reloaded chat looks the same as a live one. A direct reply (no agent chain) carries `direct`: its status line, the model and the time.

## Runs

A run has an id and keeps every event in order, each numbered by `seq` from 1 (a `RunEvent`, ADR-0035 §3), so the chat and every run screen read the same run.

- **Following.** `followRun(id, after)` gives the events after `after`, then each new one as it happens. It stays open while the run waits for sign-off, and ends when the run ends (`done`, `stopped` or `error`) or the signal aborts.
- **A dropped connection.** A follow that ends before the run did lost its connection. `watchRun(source, id, after, { signal, retryMs, onreconnecting })` in [`runs.ts`](../../apps/web/src/lib/data/runs.ts) waits a second and follows again after the last `seq` it saw, so nothing is missed or repeated. It calls `onreconnecting(true)` when the follow drops and `onreconnecting(false)` when it follows again, so the status line can say so.
- **Opening a run again.** A chat keeps the questions asked in it: opening it again shows each answer as far as its run has got, and the chat follows a live one after its last event. The run view does the same with `getRun`.
- **Who decided** is the signed-in person; a screen never names them.
- **The fake's runs** play at real pace whether anyone follows them or not. A question about rounding plays a Challenger FAIL and a replan; about the server being down, an error at the Analyst; about the connection dropping, a run whose first follow drops just after the Analyst starts. The stored chats' runs are `run-demo` and `run-0142`.

## Stream events

Events arrive in order, each with its run's `seq`. `at` is the server's time in milliseconds.

| `type` | Carries | Shown as |
| --- | --- | --- |
| `status` | `stage` (one of the six roles, or `replan`), `description`, optional `done` | the stage rail and the live status line |
| `delta` | a piece of the answer's markdown | the answer text, streamed |
| `tool` | a `ToolCall`: id, name, input, output, state (`running`, `done`, `failed`); a repeated id updates the call | the tool-call row |
| `source` | a `Source`: citation number, title, passage, and the `evidenceId` it was read from when there is one | the `[n]` citations and the sources list; the run view links evidence to its review |
| `sign-off` | the checks for the person to review, each with a verdict and the citation numbers it rests on (`cites`), and on a later try a `revision` (try number, objections, removed and added lines) | the sign-off panel and its changes view; the receipt's revision card |
| `decision` | `released` or `withheld`, who decided, and for a return the `reason` | the Sign-off node (noting `returned` for a return), the run view's Sign-off stage and, for a return, a line under the answer |
| `receipt` | fingerprint, model, `seconds` (the agents' working time, as the status line sums it), source count, who signed, external calls observed, `folds` (titled markdown: full provenance and each agent's own output), and the record: `classification`, `pack` (name, version, hash), `routing` (each role's model), `skills` (with version hashes), the `ledger` position and the `deliverables`, each a `FileInfo` (name, kind, size, hash, classification and state) | the receipt labels, then the folds and the details panel's Receipt tab; the execution timeline fold is built from the status events |
| `done`, `stopped`, `error` | error: the server's `message` and optional plain-language `advice` | the end of the run; an error shows the run error card, which reads the cause from those two fields |

## The six roles

`planner`, `reader`, `analyst`, `author`, `challenger` and `sign-off`. The stage rail draws Planner, Analyst, Author, Challenger and Sign-off, as the running app does; Reader's work shows in the status line and its tool calls. The rail's states are derived by `deriveRun` in [`stages.ts`](../../apps/web/src/lib/data/stages.ts), following the running app's rules:
- A stage's segment opens at its first status event and closes at the next stage's event, a `done` status, or the end of the run.
- `replan` counts a re-plan: Analyst, Author and Challenger then run again.
- A Challenger description containing "fail" or "pass" sets its verdict.
- `done` after the Sign-off stage with no decision means released.

`stageDetails` in the same file gives the run view what each rail stage did: its status lines with the time since the run started and the try they belong to (each `replan` starts the next try, and its own line goes to the stage that sent the work back), the tool calls and sources found while it worked, with the Reader's in the Analyst's stage, and the text it drafted.

## Known limits for runs from the server

The fake's runs are simple enough that these hold today; a server's runs will need each settled.

- **Answer text joins every try's deltas.** The chat's answer, the run view's text, `stageDetails`' Author text and the fake's `getChat` all append every `delta`. That is right only because the fake's first try streams no deltas. A server that streams both drafts needs a rule, such as starting over at each `replan` or keeping only the deltas after the last one.
- **Sources are listed once per stage, not once per run.** The run view gathers each stage's sources, so two stages reporting the same citation number would list it twice.
- **A refused cancel isn't handled.** The run view's Cancel and the chat's Stop don't expect `cancelRun` to reject. The fake never does; a server can.

## Planned

The generated API client and the WebSocket (the rest of WP-UI-05, after the server's run endpoints in WP-RT-01) and paging through the chat list are planned. Following a run and resuming after the last event work against the fake source today ([WP-UI-05, part 1](frontend.md#wp-ui-05-part-1-runs-in-the-fake-source-followed-from-the-last-event)). Only the session calls are on the server so far.
