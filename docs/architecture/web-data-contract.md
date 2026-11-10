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
| `adminLedger()` | every admin change, newest first (`LedgerEntry`: when, by whom, action, target; never a password) | the admin pages' change trail |
| `getProfile()` / `saveProfile(profile)` | the person's profile (`Profile`: name, bio, gender, birth date, avatar kind, user variables); saving the name renames the signed-in person | the Account page |
| `changePassword(current, next)` | changes the password; both go only to the backend, never logged, stored or put in a URL | the Account page |
| `getUsage()` | the person's usage (`Usage`): totals, a per-day heat map with weekly and running totals, insights, top models and tools; token counts are estimates | the Usage page |
| `exportChats()` / `importChats(chats)` / `archiveAllChats()` / `deleteAllChats()` | every chat with its messages (archived included) for a JSON export; importing adds chats and returns how many; archiving hides them from `listChats()` | the Data Controls page |
| `listArchivedChats()` / `unarchiveChat(id)` / `unarchiveAllChats()` / `deleteChat(id)` | archived chats newest first; unarchiving returns a chat to `listChats()`; deleting removes it for good | the Archived Chats page |
| `listMemories()` / `addMemory(draft)` / `updateMemory(id, draft)` / `deleteMemory(id)` / `clearMemories()` | the person's memories (`Memory`: content, type `user` or `context`, optional path, updated time), most recently changed first | the Personalization page |
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
