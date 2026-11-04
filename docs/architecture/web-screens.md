---
title: Web screens
type: architecture
status: planned
owner: R3
updated: 2026-10-08
covers:
  - apps/web/src/routes/
tags: [4ce, architecture, frontend]
---

# Web screens

The inventory of every screen in `apps/web`: what it is for, who uses it, what it is built from, what data it needs, which backend work it waits on, its states, and when it ships. This is step 2 of the frontend plan. It builds on [ADR-0035](../adr/0035-frontend-foundations.md) and uses the components, tokens and states of the [design system](design-system.md). Everything here is **planned**: no screen exists yet.

Section numbers (§) refer to the master plan (v3.8). Work package ids (WP) are the plan's §12 ids; new ones are proposed at the end.

## How to read this page

**Milestones** (§11.3):

- **M1:** neutral parity, end of week 9.
- **M2:** the universal pitch build and investor demo, end of week 18.
- **Later:** M3 or after. Listed so the routes and the shell leave room for them.

**Demo steps** are the six steps of the pitch demo (§13.7):

1. Sovereignty page.
2. First sector pack: a photo of a handwritten log becomes boxed observations, verdicts cite clauses, a value is calculated, the Challenger catches a seeded wrong figure and the run replans, the `<Gate role>` types `approve`, and a signed deliverable with a QR code comes out.
3. Switch to the second sector pack live: two documents become observations, two values are calculated in code, the verdict is REVIEW with its clause, and a second person approves.
4. Cross-sector pack: an `authority` rule (§7.9) routes the approval to a higher `<Gate role>`.
5. Verification: a QR code opens the verification page; an evidence pack verifies offline on a second machine.
6. Pack Studio: a limit changes, the pack's tests run, and the new version is signed into the ledger.

**Who uses a screen** is given two ways, because the plan uses "role" for both:

- **People** are access roles (§7.3): Admin, Author (starts runs), Reviewer (approves), Viewer, Auditor, Pack Author, Pack Approver, and Skill Approver (§7.27). Packs rename them; the UI always shows the pack's label.
- **Run roles** are the six roles whose work a screen shows (ADR-0035 §5): Planner, Reader, Analyst, Author, Challenger, Sign-off. Router is internal and never shown.

**Placeholders.** Screens never name a sector. Labels come from the active pack's vocabulary at run time:

| Placeholder       | Means                                                         |
| ----------------- | ------------------------------------------------------------- |
| `<Subject>`       | The pack's word for a subject (§7.2), singular                |
| `<Subjects>`      | Its plural                                                    |
| `<Gate role>`     | The pack's name for the person who signs off (core: Reviewer) |
| `<Document kind>` | A pack-defined document kind (§7.8)                           |
| `<Pack>`          | A pack's title                                                |

Fixture data in `apps/web` uses neutral values only: rule `R2`, parameter `Ratio`, units `s`, `%` and `₹`, ids like `CASE-0142`.

**States.** Every screen lists these five. They use the design system's state rules; this page only says what each one shows on that screen.

| State   | Meaning on a screen                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------ |
| empty   | Nothing to show yet. A static signature icon, a one-line title, one line saying what was checked, and at most one action.      |
| loading | Skeletons where the layout is known; the six-dot ring after 300 ms; elapsed time after 10 s.                                   |
| error   | A `stop` message with an icon and one way forward. "Could not check" uses the `unverified` glyph and is never shown as a pass. |
| live    | Something is changing now: a run, an ingest, a test run, a monitor. Violet working state, one moving thing per region.         |
| decided | A human or the Rule Engine has settled it: released (ink ring, tick) or withheld (dash); sealed items are read-only.           |

A screen that cannot reach a state says so with "n/a".

**Devices** (ADR-0035 §6). Every screen is built for desktop (1024 px and wider). Tablets (768–1023 px) get the screens for review, sign-off and capturing evidence, marked "tablet" below; on other screens a tablet gets the desktop layout without tablet-specific work. Phones are later.

## Our components, by behaviour

These are 4CE's own components, rebuilt from their behaviour on the new tokens (ADR-0035 §14). Screens below refer to them by name. Base components (buttons, fields, menus, dialogs, `DataTable`, the command palette) are in the design system.

- **Stage rail.** A line of nodes for the run's workflow, in the order the pack's workflow sets (§7.11).
  - The moving light hands over from one node to the next (`handover`); the current node shows the working dots; a finished node's ring closes (`deliberate`).
  - The human gate is ink, never violet.
  - It is a pure function of run state, so a reload, a dropped connection or a second tab shows the same rail (ADR-0035 §3).
  - ←/→ move across nodes; Enter opens that stage's detail. Under reduced motion every node shows its still frame. In print it is one static line.
  - A replan after a Challenger FAIL adds a second pass after the failed node; the first pass stays visible and marked.
- **Node glyph.** One stage's state as a ring plus a word: not reached, working, done, failed, waiting for a person (the `sign-off-pending` glyph), withheld. The word is the accessible name.
- **Status line.** One line under the rail saying what is happening in plain words. It holds each message for at least `ambient` and is a polite live region, so screen readers hear stage changes, not every token.
- **Sign-off panel.** A docked panel at the human gate.
  - It shows exactly what will be released: the text that is fingerprinted, the verdicts, the checks, the Challenger's result and the classification, plus the fingerprint and which `<Gate role>` may approve.
  - Release needs the typed word `approve` in every language, guarded against input-method composition, then a confirm. The panel explains the word in the active language.
  - **Return** sends the work back with a reason. Nothing is released by any other path (§7.15, fail-closed).
  - It is fully operable by keyboard and screen reader (ADR-0035 §9).
- **Receipt.** The record of a decided run: fingerprint (8 hex characters plus `…`, full on expand, copyable), who decided and when (with time zone), classification, `pack@version` and pack hash, models and the routing table, skills used with version hashes, the egress count during the run, the checks, the ledger position, deliverables as file cards, and (M2) the QR code and the evidence-pack export.
- **Audit sheet.** The receipt as a printed A4 record, following the design system's print rules: header, classification banner, approval block, full fingerprint in groups of four, footer with ledger position and QR code.
- **File card.** One file, uploaded or produced: a neutral type tag with a Phosphor file icon, name, size, hash prefix, classification, and its state (uploading with progress, scanning, parsing, ready, failed). Opens or downloads.
- **Revision card.** One version of a deliverable: what changed since the previous version as diff marks, who and when, and its fingerprint. Versions stack newest first.
- **Run error card.** A run that stopped: the stage, the reason in plain words (budget exceeded, model unavailable, policy denied with the policy id and reason, cancelled), what was spent, and that nothing was released. One action: retry, or open the run.
- **Sovereignty view.** The sovereignty facts as one block: external connections counted, canary result, and any connector switched on (amber). It appears on the Sovereignty page and, compact, on every receipt.
- **Logo motion.** The 4CE mark's own motion, played once on sign-in and used as the app's loading mark. It animates the existing mark and never redraws it. Reduced motion shows the final frame.
- **Evidence viewer.** A page image with numbered observation boxes drawn over it, kept in step with a list of the observations. Selecting a box selects its row and the reverse. Zoom and pan work by keyboard as well as pointer.
- **Verdict badge.** A verdict glyph plus its word (PASS, REVIEW, FAIL, NO DATA), never colour alone.
- **Classification banner.** The level (§7.5) in the pack's words, at the top of anything that carries classified content and on every print.

## Route map

Every route in one table. Details follow, grouped by area. `[id]` segments are opaque ids; nothing personal goes into a URL.

| Route                                    | Screen                             | Milestone | Demo step | WP           |
| ---------------------------------------- | ---------------------------------- | --------- | --------- | ------------ |
| `/sign-in`                               | Sign-in                            | M1        | —         | UI-06        |
| (layout)                                 | App shell, command palette         | M1        | all       | F-09         |
| (error page)                             | Not found, no access, server error | M1        | —         | UI-06        |
| `/ui`, `/ui/motion`                      | Component gallery, motion preview  | M1        | —         | F-09         |
| `/`                                      | New chat                           | M1        | 2, 3, 4   | UI-01        |
| `/chat/[chatId]`                         | Conversation                       | M1        | 2, 3, 4   | UI-01        |
| `/runs/[runId]`                          | Run view                           | M1        | 2, 3, 4   | UI-01, UI-03 |
| `/runs/[runId]/assessment`               | Assessment and calculations        | M1        | 2, 3, 4   | UI-08        |
| `/runs/[runId]/sign-off`                 | Run view with the sign-off panel   | M1        | 2, 3, 4   | UI-02, UI-10 |
| `/runs/[runId]/audit`                    | Audit sheet (print)                | M1        | 2         | UI-03        |
| `/cases`                                 | `<Subjects>`: case list            | M1        | 2, 3      | UI-01        |
| `/cases/[caseId]`                        | Case                               | M1        | 2, 3      | UI-01        |
| `/evidence/[evidenceId]`                 | Evidence review                    | M1        | 2, 3      | UI-07        |
| `/approvals`                             | Approval queue                     | M2        | 3, 4      | UI-10        |
| `/verify/[fingerprint]`                  | Verification (from a QR code)      | M2        | 5         | UI-11        |
| `/ledger`                                | Ledger                             | M2        | 5, 6      | UI-12        |
| `/sovereignty`                           | Sovereignty                        | M1        | 1         | UI-04        |
| `/knowledge`                             | Collections                        | M1        | —         | UI-09        |
| `/knowledge/[collectionId]`              | Collection and upload              | M1        | —         | UI-09, UI-17 |
| `/packs`                                 | Pack registry                      | M2        | 3         | UI-13        |
| `/packs/[packId]`                        | Pack detail                        | M2        | 3, 6      | UI-13        |
| `/studio`                                | Pack Studio home                   | M2        | 6         | UI-14        |
| `/studio/[packId]`                       | Pack Studio draft workspace        | M2        | 6         | UI-14        |
| `/studio/[packId]/rules/[ruleId]`        | Rule editor                        | M2        | 6         | UI-14        |
| `/studio/[packId]/sign`                  | Save and sign a version            | M2        | 6         | UI-14        |
| `/admin/users`                           | Users and roles                    | M2        | —         | UI-15        |
| `/admin/skills`                          | Skills                             | M2        | —         | SK-05        |
| `/admin/skills/[skillId]`                | Skill detail                       | M2        | —         | SK-05        |
| `/admin/notices`                         | Third-party notices                | M2        | —         | UI-16        |
| `/approvals/delegation`                  | Delegation                         | Later     | —         | UI-18        |
| `/ledger/checkpoints`                    | Signed checkpoints                 | Later     | —         | UI-23        |
| `/knowledge/[collectionId]/[documentId]` | Document detail with Deep Cache    | Later     | —         | UI-25        |
| `/cases/[caseId]/trends`                 | Trends over a case's history       | Later     | —         | UI-26        |
| `/packs/install`                         | Install or upgrade a pack          | Later     | —         | UI-21        |
| `/studio/[packId]/documents` and more    | Pack Studio v2                     | Later     | —         | UI-22        |
| `/studio/skills`                         | Skill Studio                       | Later     | —         | SK-05        |
| `/admin/views`                           | Business views                     | Later     | —         | UI-19        |
| `/admin/policies`                        | Policies                           | Later     | —         | UI-20        |
| `/admin/connectors`                      | Data and cloud connectors          | Later     | —         | UI-24        |
| `/ops`                                   | Operations dashboards (Grafana)    | M1        | —         | OB-01        |

`/ops` is Grafana behind the 4CE login (§7.23). It keeps its own name and logo; `apps/web` only links to it from the admin navigation.

## Shell and sign-in

### `/sign-in`: Sign-in

- **Purpose:** a person signs in with a local account and lands where they were going.
- **People:** everyone. **Run roles:** none.
- **Components:** logo motion (once), username and password fields with paste and autofill allowed (WCAG 3.3.8), one primary button, inline error.
- **Data:** a server-side session as an HttpOnly, SameSite=Strict cookie, and the CSRF token for writes (§7.3, ADR-0035 §2). The return path is kept in memory, never in the URL query.
- **Depends on:** WP-ID-01.
- **States:**
  - empty: the form.
  - loading: the button keeps its label and gains the six-dot ring.
  - error: wrong details; locked out after repeated failures, with when to try again; server unreachable.
  - live: n/a.
  - decided: signed in, then redirect.
- **Milestone:** M1. **Demo step:** precondition for all. **Tablet:** yes.

### (layout): App shell

- **Purpose:** the frame every signed-in screen sits in: navigation, the active pack, the person, and global keys.
- **People:** everyone; navigation items are filtered by access role. **Run roles:** none.
- **Components:**
  - navigation with the pack's labels (Chat, `<Subjects>`, Approvals, Knowledge, Ledger, Sovereignty, Packs, Studio, Admin), each shown only to roles that may open it
  - the pack switcher (M2, WP-UI-13) showing the working pack's title and risk tier
  - an approvals count (M2)
  - the person menu: theme, motion, density and language (stored under `4ce.theme`, `4ce.motion`, `4ce.density`, `4ce.locale`), and sign out
  - the command palette (Ctrl+K or ⌘K) and the shortcut sheet (`?`)
  - a session banner when the connection drops or the session is about to expire
- **Data:** the session's person, access roles and groups; the active pack's vocabulary (labels per locale); the pending-approvals count (M2).
- **Depends on:** WP-F-09, WP-ID-02, WP-PK-04 (vocabulary), WP-UI-05.
- **States:**
  - empty: n/a.
  - loading: the shell's frame with skeleton navigation until the session resolves.
  - error: server unreachable (a banner with a retry; the current screen stays readable); session expired (back to sign-in, keeping the path).
  - live: reconnecting after a dropped WebSocket, then resuming (ADR-0035 §3).
  - decided: n/a.
- **Milestone:** M1, with the pack switcher and approvals count at M2. **Demo step:** all; step 3 uses the pack switcher. **Tablet:** yes.

### (error page): Not found, no access, server error

- **Purpose:** say plainly that a page does not exist, that the person's role may not open it, or that the server failed, and offer one way on.
- **People:** everyone. **Run roles:** none.
- **Components:** the empty-state pattern with a Phosphor glyph; the role the page needs (for no access); a link home.
- **Data:** the status code and, for no access, the required role from the route guard.
- **Depends on:** WP-ID-02 (route guards).
- **States:** empty: the message itself. loading, live, decided: n/a. error: this page is the error state.
- **Milestone:** M1. **Demo step:** —. **Tablet:** yes.

### `/ui` and `/ui/motion`: Component gallery and motion preview

- **Purpose:** render every component in every state, light and dark, reduced motion, Hindi and print; preview every motion on a scrubber before it is built (ADR-0035 §13, design system Motion).
- **People:** the team. Not linked from navigation. **Run roles:** all six, as fixtures.
- **Components:** every base and 4CE component; a scrubber for the signature motions (rail handover, working dots, ring closing, mark drawing, light pass, logo).
- **Data:** fixtures only.
- **Depends on:** WP-F-09.
- **States:** every component's own states are the content. The page itself has none.
- **Milestone:** M1, grown with every component. **Demo step:** —; its snapshots guard the demo screens. **Tablet:** checked at tablet width.

## Chat and runs

### `/`: New chat

- **Purpose:** start a request: ask a question, attach evidence, or ask for work on a `<Subject>`.
- **People:** Author (anyone who may start runs); Viewer can ask questions where policy allows. **Run roles:** Planner, once sent.
- **Components:** the composer (text, attachments as file cards, an optional `<Subject>` picker), recent conversations, and the working pack shown beside the composer.
- **Data:** recent conversations; the working pack; the `<Subjects>` the person may see (for the picker); upload limits.
- **Depends on:** WP-RT-01, WP-RT-02 (task type and workflow from pack intents), WP-KN-01 (uploads), WP-DM-01.
- **States:**
  - empty: no conversations yet; one line on what 4CE can do with the working pack.
  - loading: skeleton list of recent conversations.
  - error: an upload refused (type, size, scan) on its file card; the server unreachable.
  - live: attachments uploading on their file cards.
  - decided: n/a; sending opens the conversation.
- **Milestone:** M1. **Demo step:** 2, 3 and 4 start here. **Tablet:** yes, to attach a photo as evidence.

### `/chat/[chatId]`: Conversation

- **Purpose:** the thread of a conversation, where answers stream in and each piece of work appears as a run with its own rail.
- **People:** the Author who started it, and anyone it is shared with by policy. **Run roles:** all six, as each run reaches them.
- **Components:**
  - messages, with answers in `body` type and numbered citations `[n]` that open the cited passage
  - a compact stage rail and status line per run, linking to the run view
  - file cards for attachments and deliverables
  - a run error card when a run stops
  - an "unreviewed skill" marker on answers that used a draft skill (M2, §7.27)
  - the "decision support: a qualified person decides" banner when the pack is tier 3 (§4.5)
- **Data:** messages; for each run its state and live events (one WebSocket, events numbered per run); citations with passage text; files.
- **Depends on:** WP-RT-01, WP-RT-02, WP-RT-05, WP-KN-03 (numbered sources), WP-UI-05 (live events).
- **States:**
  - empty: a new conversation with only the composer.
  - loading: skeleton messages with real line heights.
  - error: a run error card in the thread; "the documents don't cover this" when the relevance guard drops every passage (§7.7); the connection lost, then resumed from the last event.
  - live: an answer streaming; a run moving along its rail.
  - decided: a run released or withheld, shown by its node glyph and a link to the receipt.
- **Milestone:** M1. **Demo step:** 2, 3, 4. **Tablet:** yes, for review.

### `/runs/[runId]`: Run view

- **Purpose:** one run in full: where it is, what each stage did, what was checked, and its receipt once decided.
- **People:** the Author, Reviewers who may decide it, Auditors (read-only). **Run roles:** all six.
- **Components:**
  - the full stage rail and status line; each node opens its stage's detail below the rail
  - stage details: the Planner's task type and workflow, the routing table (§7.6), the Reader's observations (linking to evidence review), the assessment (`/runs/[runId]/assessment`), the Author's draft, the checks (§7.14) and the Challenger's verdict with one line per claim
  - "could not check" shown with the `unverified` glyph, never as a pass
  - a cancel action while the run is live (§7.11)
  - the run error card, and the receipt once decided
- **Data:** run state from the run store, then live events after the last sequence seen (ADR-0035 §3); routing table; checks; Challenger output; budgets spent.
- **Depends on:** WP-RT-01, WP-RT-03, WP-RT-04, WP-RT-05, WP-RT-06, WP-MD-03, WP-RT-07 (receipt).
- **States:**
  - empty: n/a; a run always has a plan.
  - loading: the rail's frame with not-reached nodes while state loads.
  - error: the run error card in place of the next stage; a Challenger FAIL followed by a replan, shown as a second pass on the rail.
  - live: one node working, the light handing over; the status line saying what is happening.
  - decided: released (ink ring with tick) or withheld (dash); everything read-only, with the receipt.
- **Milestone:** M1. **Demo step:** 2 (the seeded fault caught and the replan), 3, 4. **Tablet:** yes, for review.

## Cases and subjects

### `/cases`: `<Subjects>`

- **Purpose:** find a `<Subject>` and its case, or create one.
- **People:** Author, Reviewer, Viewer, Auditor, within what policy lets each see. **Run roles:** none.
- **Components:** `DataTable` at default density (identifier, `<Subject>` type, pack, latest verdict badge, awaiting sign-off, last activity); filter chips by pack, type and status; a "New `<Subject>`" dialog whose fields come from the pack's subject schema.
- **Data:** cases with their subject's identifiers and pack-defined attributes; the pack's subject types and schema per locale.
- **Depends on:** WP-DM-01, WP-PK-04.
- **States:**
  - empty: no `<Subjects>` yet for this pack; one action: New `<Subject>`.
  - loading: skeleton rows.
  - error: the list failed to load; a create refused by the pack's schema, shown on the field.
  - live: n/a.
  - decided: n/a; per-row status shows each case's latest decision.
- **Milestone:** M1. **Demo step:** 2, 3 (the working pack's word replaces "`<Subjects>`" when the pack switches). **Tablet:** yes, for review.

### `/cases/[caseId]`: Case

- **Purpose:** a `<Subject>`'s history in one place: its evidence, observations, runs, assessments, approvals and deliverables over time (§7.2).
- **People:** as for the list. **Run roles:** all six, through the runs listed.
- **Components:**
  - a header with the identifiers and attributes, and the classification banner
  - a timeline (Phosphor `clock-counter-clockwise`) of evidence added, runs, verdicts and approvals, newest first
  - tabs: Evidence (file cards, an "Add evidence" dialog with camera capture on tablets), Observations (`DataTable`, compact: subject, parameter, value and unit, rule applied, verdict, link to its page and box), Runs (compact rails), Deliverables (revision cards)
- **Data:** the case and its subject; evidence with classification; observations with provenance; runs; assessments with pack hashes; approvals; deliverable versions.
- **Depends on:** WP-DM-01, WP-RD-01, WP-RL-01, WP-SO-01, WP-DL-01, WP-KN-01 (evidence upload).
- **States:**
  - empty: a new case with no evidence; one action: Add evidence.
  - loading: header skeleton, then the timeline.
  - error: the case failed to load; no access to it (the no-access page).
  - live: a run on this case is in progress (its compact rail moves); evidence uploading or being read.
  - decided: released items carry the sealed icon and are read-only.
- **Milestone:** M1. **Demo step:** 2, 3. **Tablet:** yes, for review and capturing evidence.

### `/cases/[caseId]/trends`: Trends over a case's history (later)

- **Purpose:** one parameter's values across the case's evidence over time, with the `trend` rule that judged them (§7.2, §7.9).
- **Depends on:** WP-DM-01; `trend` rules are Phase 2 (no WP id beyond WP-RL-01's first six types).
- **States:** empty: fewer readings than the rule needs. loading: chart skeleton. error: readings in different dimensions refused. live: n/a. decided: the trend rule's verdict, sealed once released.
- **Milestone:** later. **Demo step:** —. **Tablet:** no.

## Evidence review

### `/evidence/[evidenceId]`: Evidence review

- **Purpose:** check what was read from a piece of evidence against the page itself, and verify or correct each observation before rules use it.
- **People:** Author and Reviewer verify and correct; Viewer and Auditor read. **Run roles:** Reader (who read it).
- **Components:**
  - the evidence viewer: the page image (rendered at the core kind's size, §7.8) with numbered observation boxes; page navigation; zoom and pan
  - the observation list in step with the boxes: number, parameter label, value and unit, confidence, and the dashed `observation-unsure` glyph with "check" on anything read with less than full confidence
  - per observation: **Verify** (accept as read) and **Correct** (enter the right value and unit; the unit must be in the parameter's dimension, §7.9)
  - who verified each one and when; the `<Document kind>` it was read as
  - deep links: `?page=` and `?box=` open a page with one box selected, so the assessment and the case can point at the exact box
- **Data:** page renders; observations with box, page, value, unit, confidence, extractor model and version, and verification state; the pack's extraction schema labels per locale; parameter units.
- **Depends on:** WP-RD-01, WP-DM-01, WP-PK-04 (units), WP-LG-01 (`observation.verified` entries).
- **States:**
  - empty: nothing was read from this page, with what was looked for (the `<Document kind>`'s fields).
  - loading: the page area keeps the page's aspect ratio as a still block; boxes appear with the image.
  - error: the render failed or the reading failed ("could not read", with the `unverified` glyph); a correction refused for a wrong unit, shown on the field.
  - live: the Reader still reading; observations appear one at a time, numbered in reading order.
  - decided: an observation used by a released assessment is sealed: read-only, with who verified it.
- **Milestone:** M1 (today's reading flow, §7.8, must reach parity). **Demo step:** 2 (the handwritten photo becomes boxed observations), 3 (two documents read). **Tablet:** yes, for review and capturing evidence.

## Rules and assessments

### `/runs/[runId]/assessment`: Assessment and calculations

- **Purpose:** show how the rules decided: each verdict with the value it used, the limits, the clause and the pack version, and every calculation step with units. The model never issues a verdict (§4.6).
- **People:** Author, Reviewer, Auditor. **Run roles:** none; this is deterministic work, shown inside the run.
- **Components:**
  - the verdicts as a compact `DataTable`: rule id, parameter, value and unit (linking to its evidence box), limits with unit and tolerance, verdict badge, clause, disposition, `pack@version` and pack hash; rows expand inline to show the rule's bands or expression
  - calculations: inputs with units, each step as written, the output with its unit, and a link to the workbook deliverable
  - an `authority` result as its own block: the value, the matrix row that matched, the clause, and the `<Gate role>` it requires
  - in tier 3, a NO DATA verdict marked as blocking release (§7.4)
- **Data:** the assessment (verdicts, clauses, dispositions, pack hash per verdict); observations used; calculations with steps; the rule definitions for inline expansion.
- **Depends on:** WP-RL-01, WP-CA-01, WP-RT-04, WP-PK-02.
- **States:**
  - empty: no rules applied to this run (an `ask` or `chat` run), saying which task type it was.
  - loading: skeleton rows.
  - error: a value refused for a wrong dimension (§7.9), shown on its row; a rule pack failed to load.
  - live: verdicts arrive row by row while the deterministic stage runs.
  - decided: once the run is released, the table is sealed.
- **Milestone:** M1 for band, enum, presence, expression, date and authority; the Phase 2 rule types (membership, aggregate, trend, require_evidence, cross) show in the same table at M2. **Demo step:** 2 (verdicts with clauses, a calculated value), 3 (two values calculated, REVIEW with its clause), 4 (the authority result). **Tablet:** yes, for review.

The rulebook itself, read-only, is a tab of the pack detail (`/packs/[packId]`). Editing rules is Pack Studio.

## Approvals

### `/runs/[runId]/sign-off`: Run view with the sign-off panel

- **Purpose:** a named person decides whether the run's work is released. Only the typed word `approve` releases it (§7.15).
- **People:** Reviewer, shown as the pack's `<Gate role>`; the Author sees the panel's state but may not act where maker-checker applies. **Run roles:** Sign-off.
- **Components:** the run view with the sign-off panel docked; the review it shows is exactly what is fingerprinted, and that same review is what the approval records.
- **Data:** the pending approval: what will be released and its fingerprint, the verdicts and checks, the Challenger's verdict, the classification, the risk tier, who may approve and why (role, maker-checker, two-person rule, authority result).
- **Depends on:** WP-SO-01, WP-RT-07, WP-LG-01 (`approval.decision`); the M2 states also need the policy engine (§7.4), which has no WP id in §12.
- **States:**
  - empty: n/a; the panel only opens at the human gate.
  - loading: the panel's frame while the review loads; the approve control stays disabled until the whole review has loaded.
  - error: release blocked by policy (for example NO DATA in tier 3), naming the policy and reason; the word mistyped (the control stays disabled, no error flash); the submit failed (nothing released, retry).
  - live: waiting for a decision; another tab or person deciding first updates this panel at once.
  - decided: approved (ink ring with tick, then the receipt) or returned (the `sign-off-returned` glyph and the reason).
- **M2 states (WP-UI-10):** "you started this run, so someone else must approve" (maker-checker); "approved once, waiting for a second person" (two-person rule); "this needs a higher `<Gate role>`" (authority).
- **Milestone:** M1 for the fail-closed panel; M2 for the maker-checker, two-person and authority states. **Demo step:** 2, 3, 4. **Tablet:** yes.

### `/approvals`: Approval queue

- **Purpose:** every pending approval a person may decide, durable across reloads and restarts, oldest first.
- **People:** Reviewer; the Author sees approvals they asked for. **Run roles:** Sign-off.
- **Components:** `DataTable` at comfortable density: what (run and `<Subject>`), pack, classification, `<Gate role>` required, requested by, waiting since, state (pending, needs a second person, needs a higher `<Gate role>`); filter chips "For me to decide" and "I asked for". A row opens `/runs/[runId]/sign-off`.
- **Data:** pending approvals the person may see and decide, with the reason each one is routed to them.
- **Depends on:** WP-SO-01, WP-ID-02; routing by role and authority needs the policy engine (no WP id).
- **States:**
  - empty: nothing waiting for you, and what was checked (your `<Gate role>`s).
  - loading: skeleton rows.
  - error: the queue failed to load.
  - live: a new request arrives as one new row; a decided row leaves.
  - decided: decided approvals leave the queue; their record is on the run's receipt.
- **Milestone:** M2. **Demo step:** 3 (a second person finds and approves the work), 4 (the approval waits for a higher `<Gate role>`). **Tablet:** yes.

### `/approvals/delegation`: Delegation (later)

- **Purpose:** hand one's approvals to a named person for a period that expires on its own (§7.15).
- **People:** Reviewer; Admin sees all delegations. **Run roles:** Sign-off.
- **Components:** a form (delegate, `<Gate role>`s covered, start, end) and a list of active and expired delegations. Re-authentication at approval (WebAuthn, §7.15) lands with it.
- **Data and depends on:** WP-SO-01; delegation and the policy admin are Phase 3 (§11.2).
- **States:** empty: no delegations. loading: skeleton list. error: an overlapping or self delegation refused. live: n/a. decided: an expired delegation, read-only.
- **Milestone:** later (M3). **Demo step:** —. **Tablet:** no.

## Deliverables and receipt

### Receipt and deliverables (in `/runs/[runId]` and `/cases/[caseId]`)

- **Purpose:** the proof of a decided run, and the documents it produced, where people already look: the end of the run view and the case's Deliverables tab.
- **People:** Author, Reviewer, Viewer, Auditor. **Run roles:** Author (the draft), Challenger (its verdict), Sign-off (the decision).
- **Components:** the receipt with the compact sovereignty view; deliverables as file cards (docx, xlsx, pptx, §7.17); revision cards for each version with diff marks; provenance (sources `[n]`, observations, rule packs) as expandable rows; at M2 the QR code and an **Export evidence pack** action.
- **Data:** the release: fingerprint, approver, time, ledger position, classification, pack versions and hashes, models and routing, skills with version hashes, egress count, checks; deliverable files and versions.
- **Depends on:** WP-RT-07, WP-DL-01, WP-LG-01, WP-SV-01 (egress count); M2: QR codes and the evidence pack (§7.16), which have no WP id in §12.
- **States:**
  - empty: a withheld run has no deliverable; the receipt says it was withheld, by whom and why.
  - loading: the receipt's frame with skeleton lines.
  - error: a deliverable failed to render (a run error card for the release stage); a download failed.
  - live: deliverables rendering after approval, each on its file card.
  - decided: the receipt is sealed and copyable; it never changes after release.
- **Milestone:** M1; QR code and evidence-pack export at M2. **Demo step:** 2 (a signed deliverable with a QR code), 3 (the second pack's deliverable), 5 (export the evidence pack). **Tablet:** yes, for review.

### `/runs/[runId]/audit`: Audit sheet

- **Purpose:** the decided run as a printed record that matches the Word deliverable's frame, so paper and file agree.
- **People:** Reviewer, Auditor. **Run roles:** Sign-off (the approval block).
- **Components:** the audit sheet in print styles: header with the organisation's mark and classification banner, the approval block (who, when with zone, fingerprint, the review shown), verdicts with clauses, the static rail, and the footer with print time and person, ledger position and QR code. On screen it shows a print preview with one Print button.
- **Data:** as for the receipt, plus the approval's recorded review.
- **Depends on:** WP-RT-07, WP-SO-01, WP-LG-01.
- **States:** empty: a run not yet decided has no audit sheet (it says so and links to the run). loading: page skeleton. error: failed to load. live: n/a. decided: the only state it prints in.
- **Milestone:** M1; the QR code in its footer at M2. **Demo step:** 2. **Tablet:** no.

## Verification page

### `/verify/[fingerprint]`: Verification (opened from a QR code)

- **Purpose:** someone scans the QR code on a deliverable and sees whether that exact released text is in the ledger, unchanged, and when and by whom it was released.
- **People:** anyone on the internal network who scans a code; details only for people signed in with access (see the open questions). **Run roles:** Sign-off (the release it confirms).
- **Components:**
  - one large result: `seal-check` and "Released, unchanged" (ok), or "No record of this fingerprint" (stop), or "Could not check" (`unverified`)
  - the fingerprint in full, in groups of four, copyable
  - the ledger position (from the QR code's `?at=` value) and the chain check from that entry to the latest signed checkpoint
  - for people with access: the run, the `<Subject>`, the approver and the receipt
  - a broken chain shown as a `stop` row: "entry N was changed after it was written"
- **Data:** a ledger lookup by fingerprint and position; the chain's verification from that entry to the latest checkpoint; the checkpoint's signature check.
- **Depends on:** WP-LG-01, WP-LG-02, WP-RT-07; QR codes on deliverables (§7.16, no WP id).
- **States:**
  - empty: n/a; the page always has a fingerprint to check.
  - loading: the result area with the six-dot ring and "Checking the ledger".
  - error: the server unreachable (could not check, never "valid"); a malformed fingerprint.
  - live: n/a; the check runs once per visit.
  - decided: matched and unchanged; not found; or chain broken.
- **Milestone:** M2. **Demo step:** 5. **Tablet:** yes; it is likely opened on a scanning device (see the open questions on phone width).

## Ledger and evidence pack

### `/ledger`: Ledger

- **Purpose:** read the hash chain: every recorded action, in order, with its hashes, and whether the chain is intact.
- **People:** Auditor and Admin; others see entries for runs they may see. **Run roles:** all six, as actors in entries.
- **Components:**
  - `DataTable`, compact and virtualised: sequence, time with zone, actor, type, run, input and output hash, previous-hash link, sealed marker; rows expand inline to the full hashes in groups of four and the entry's references (pack, version, pack hash, rule)
  - filter chips by entry group (Appendix B: run, decisions, calls, evidence, sign-off, packs, skills, administration), run, case and pack; `?at=` opens with one entry selected
  - a chain status line: intact up to the latest signed checkpoint, or the first broken entry as a `stop` row
- **Data:** ledger entries the person may see, paged by sequence; the chain verification result; the latest checkpoint.
- **Depends on:** WP-LG-01, WP-LG-02.
- **States:**
  - empty: no entries match these filters, naming the filters.
  - loading: skeleton rows in the table's real heights.
  - error: the chain broken (the `stop` row, never hidden); the verification could not run (could not check).
  - live: new entries append at the end while the person is at the end; otherwise a "new entries" marker.
  - decided: every entry is sealed by nature.
- **Milestone:** M2. **Demo step:** 5 (the release entry behind the QR code), 6 (the pack version signed into the ledger). **Tablet:** no.

### Evidence-pack export (from the receipt)

- **Purpose:** download one released run as a zip an auditor can verify without 4CE running (§7.16).
- **People:** Reviewer, Auditor; the export is a policy-checked action (§7.4). **Run roles:** none.
- **Components:** a dialog listing what the zip holds (the deliverable, the ledger slice, the rule packs and their hashes, the model ids, the verification report, the standalone verifier), its classification, and one Export button; then a file card for the zip.
- **Data:** the evidence pack's manifest and size; the policy decision for the export (allow, deny with reason).
- **Depends on:** evidence-pack export and verifier (§7.16, Phase 2; no WP id), WP-LG-01 (`export` entry).
- **States:** empty: n/a. loading: building the zip on its file card. error: denied by policy, naming the policy; the build failed. live: building. decided: exported, with the zip's hash.
- **Milestone:** M2. **Demo step:** 5. The offline check on a second machine uses the standalone verifier, not `apps/web`. **Tablet:** no.

### `/ledger/checkpoints`: Signed checkpoints (later)

- **Purpose:** list the signed checkpoints of the chain head and print one for safekeeping (§7.16).
- **People:** Auditor, Admin. **Run roles:** none.
- **Depends on:** WP-LG-02.
- **States:** empty: none signed yet. loading: skeleton rows. error: a signature that fails to verify, as a `stop` row. live: n/a. decided: each checkpoint is sealed.
- **Milestone:** later. **Demo step:** —. **Tablet:** no.

## Sovereignty

### `/sovereignty`: Sovereignty

- **Purpose:** show that nothing is leaving the building: external connections counted, the canary blocked, every surface audited, and anything switched on that could reach out.
- **People:** everyone may read it; Admin can re-run the canary and the audit. **Run roles:** none.
- **Components:**
  - the sovereignty view, large: the external connection count (`globe-simple-x`), the canary result, and the time of the last sample
  - the surface audit as a list: each surface (4CE's own configuration, connectors, installed packs, the bundled services' silence settings) with a verdict glyph and word
  - the default-deny firewall state; cloud connectors and the web broker, shown in amber with their allowed destinations when switched on (§7.21, §7.22)
- **Data:** egress monitor samples; canary result; surface audit results; connector and web broker state.
- **Depends on:** WP-SV-01, WP-SV-02.
- **States:**
  - empty: n/a; there is always a count, even zero.
  - loading: the blocks with skeleton values; never a zero before the first sample arrives.
  - error: the monitor not running ("could not check", never zero); a surface failing its audit (`stop`, named).
  - live: the count updating as samples arrive; a canary run in progress.
  - decided: the last audit's result, with its time.
- **Milestone:** M1. **Demo step:** 1. **Tablet:** no.

## Knowledge

### `/knowledge`: Collections

- **Purpose:** the document collections a person may see, so they know what answers can draw on.
- **People:** everyone may read what policy allows; Admin and collection owners create collections. **Run roles:** none.
- **Components:** `DataTable` at default density: name, classification (M2), documents, last ingest, owner; a "New collection" dialog.
- **Data:** collections the person may read, with counts and classification.
- **Depends on:** WP-KN-01; classification (§7.5) and row-level security at M2, which have no WP id in §12.
- **States:** empty: no collections yet; one action: New collection. loading: skeleton rows. error: failed to load. live: a collection's count changes while ingest runs. decided: n/a.
- **Milestone:** M1. **Demo step:** —. **Tablet:** no.

### `/knowledge/[collectionId]`: Collection and upload

- **Purpose:** upload documents into a collection and watch each one through ingest until it can be cited.
- **People:** collection owners and Admin upload; others read. **Run roles:** none.
- **Components:** an upload area (drop or browse) producing a file card per file with its ingest state (uploading, scanning, parsing, indexed, failed), its hash prefix and its classification; `DataTable` of documents; at M2 a classification picker per collection and an override per document (WP-UI-17).
- **Data:** documents with ingest state, content hash, kind and classification; upload limits.
- **Depends on:** WP-KN-01, WP-KN-02, WP-KN-03.
- **States:**
  - empty: no documents; one action: Upload.
  - loading: skeleton rows.
  - error: a file refused (type, size, malware-scan hook) or failed to parse, on its card, with the reason.
  - live: files moving through ingest, one state change at a time per card.
  - decided: indexed documents; a re-upload of the same content is recognised by its hash.
- **Milestone:** M1; classification controls at M2. **Demo step:** —. **Tablet:** no.

### `/knowledge/[collectionId]/[documentId]`: Document detail (later)

- **Purpose:** one document's pages, structure and, where Deep Cache is on, its stored representations with provenance (§7.7).
- **Depends on:** WP-KN-01; Deep Cache v1 (Phase 2, no WP id).
- **States:** empty: Deep Cache off for this document. loading: page skeletons. error: a representation failed, with standard retrieval still available. live: Deep Cache running. decided: n/a.
- **Milestone:** later. **Demo step:** —. **Tablet:** no.

## Packs

### `/packs`: Pack registry

- **Purpose:** the installed packs, whether each can be trusted (signatures, tests), and which ones are active.
- **People:** everyone reads; Admin and Pack Approver activate or deactivate. **Run roles:** none.
- **Components:** `DataTable`: pack (with the `pack` glyph), kind (sector or cross-sector), version, risk tier, signatures (author, approver), tests (pass count and any failure), active, dependencies. Activating asks for confirmation and shows the ledger entry it writes (`pack.activate`).
- **Data:** installed packs with manifest summary, signature state, test results and active state.
- **Depends on:** WP-PK-02, WP-PK-03.
- **States:**
  - empty: no packs installed, naming where packs come from (a signed bundle).
  - loading: skeleton rows.
  - error: a pack refused because it is unsigned or a test fails (§7.1), with which test; a dependency missing.
  - live: tests running on activation.
  - decided: active packs; each activation is in the ledger.
- **Milestone:** M2 (§11.2 puts the full registry page in Phase 3; the M2 version lists and activates only, see the open questions). **Demo step:** 3. **Tablet:** no.

### Pack switcher (in the shell)

- **Purpose:** switch the working pack live, with no restart and no code change: labels, `<Subjects>`, document kinds and intents follow the chosen pack.
- **People:** everyone who uses more than one active pack. **Run roles:** Planner (pack intents).
- **Components:** a menu in the shell listing the active packs with title and risk tier; choosing one swaps the vocabulary in place with one crossfade (`slow`, or 120 ms or less when reduced).
- **Data:** active packs; the chosen pack's vocabulary per locale.
- **Depends on:** WP-PK-02, WP-PK-04, WP-RT-02.
- **States:** empty: one active pack (the switcher shows its title, no menu). loading: the new labels load before the swap, so no screen shows mixed vocabulary. error: the pack could not load; the previous pack stays. live: n/a. decided: n/a.
- **Milestone:** M2. **Demo step:** 3. **Tablet:** yes.

### `/packs/[packId]`: Pack detail

- **Purpose:** what one pack contains and proves: its manifest, signatures, tests, rulebook and versions.
- **People:** everyone reads; Pack Author and Pack Approver use it before and after Pack Studio. **Run roles:** none.
- **Components:** a header with title, version, risk tier, locales and minimum profile; tabs for Rules (the rules `DataTable`: id, parameter, limits with unit and tolerance, clause, `pack@version` and pack hash, effective date, last fired), Vocabulary, Calculators, Tests, and Versions (each with its hash, signers and ledger position).
- **Data:** the manifest (Appendix D), contents, test results and version history.
- **Depends on:** WP-PK-01, WP-PK-02, WP-PK-03, WP-RL-01, WP-CA-01.
- **States:** empty: a tab with nothing in it (a pack with no calculators). loading: header and tab skeletons. error: failed to load; a failing test, named. live: tests running. decided: signed versions, read-only.
- **Milestone:** M2. **Demo step:** 3, 6 (the new version appears with its signature). **Tablet:** no.

### `/packs/install`: Install or upgrade a pack (later)

- **Purpose:** install a signed bundle from removable media, or upgrade one, replaying its tests before activation (§7.1).
- **Depends on:** WP-PK-02, WP-PK-03; pack upgrades with test replay are Phase 3.
- **States:** empty: nothing chosen. loading: reading the bundle. error: unsigned, a failing test, a clashing dependency. live: verifying and testing. decided: installed, with its ledger entry.
- **Milestone:** later (M3). **Demo step:** —. **Tablet:** no.

## Pack Studio v1

Pack Studio v1 covers vocabulary, rules, calculators and tests (§7.1). Every edit runs the pack's tests live, and saving produces a new signed version. Document kinds, workflows and templates are v2 (later).

### `/studio`: Pack Studio home

- **Purpose:** pick a pack to change, or continue a draft.
- **People:** Pack Author; Pack Approver sees drafts waiting for a signature. **Run roles:** none.
- **Components:** a list of packs the person may author, each with its signed version and any open draft; "Start a draft from version N".
- **Data:** packs the person may author; drafts with their base version and test state.
- **Depends on:** WP-PK-02; the Pack Studio service (Phase 2), which has no WP id in §12.
- **States:** empty: no packs this person may author, naming the role needed. loading: skeleton list. error: failed to load. live: n/a. decided: n/a.
- **Milestone:** M2. **Demo step:** 6. **Tablet:** no.

### `/studio/[packId]`: Draft workspace

- **Purpose:** change a pack's vocabulary, rules, calculators and tests in one draft, with its tests always visible.
- **People:** Pack Author. **Run roles:** none.
- **Components:**
  - tabs: Vocabulary (subject types, parameters with units, labels per locale), Rules (the rules `DataTable`, each row opening the rule editor), Calculators (inputs, steps and output with units), Tests (the pack's tests, with add and edit)
  - a test panel docked beside every tab: each test with its verdict glyph and word, re-run after every edit
  - the draft's diff against its base version, with `ok-soft` additions and `stop-soft` deletions
- **Data:** the draft's contents; live test results; the base version's contents for the diff; the pack's units registry.
- **Depends on:** WP-PK-01 (schemas validate every field), WP-PK-04, WP-RL-01, WP-CA-01; the Pack Studio service (no WP id).
- **States:**
  - empty: a fresh draft equal to its base version; "no changes yet".
  - loading: tab skeletons.
  - error: a field refused by the pack schema, on the field; a unit in the wrong dimension; a test failing, named, which blocks signing.
  - live: tests running after an edit (the test panel's working state; the edited row keeps focus).
  - decided: n/a; a draft becomes decided only by signing.
- **Milestone:** M2. **Demo step:** 6. **Tablet:** no.

### `/studio/[packId]/rules/[ruleId]`: Rule editor

- **Purpose:** change one rule, for example a band's limit, and see at once which tests pass or fail.
- **People:** Pack Author. **Run roles:** none.
- **Components:** the rule's parameter and type; for a band, one row per band with its limit and unit, verdict badge, clause and disposition; for other types, their own fields (§7.9); the tests that exercise this rule beside it; the change against the signed version as diff marks.
- **Data:** the rule; the parameter's unit; tests that reference the rule and their live results.
- **Depends on:** WP-RL-01, WP-PK-04; the Pack Studio service (no WP id).
- **States:** empty: n/a. loading: field skeletons. error: a limit with no unit or the wrong dimension; overlapping or missing bands; a test now failing. live: the rule's tests re-running. decided: n/a.
- **Milestone:** M2 (the demo's edit: one limit in one rule). **Demo step:** 6. **Tablet:** no.

### `/studio/[packId]/sign`: Save and sign a version

- **Purpose:** turn a draft whose tests all pass into a new signed version, recorded in the ledger.
- **People:** Pack Author signs as author; Pack Approver adds the approver's signature that makes it installable (§7.1). **Run roles:** none.
- **Components:** the full diff; the test summary (all must pass); the new version number (semantic, §7.1); **Sign** for the author; for the approver, the same fail-closed pattern as the sign-off panel (proposed: the typed word `approve`); then the new version's hash and its ledger position.
- **Data:** the draft's diff and test results; the signing result: version, hash, signers, ledger entry.
- **Depends on:** WP-PK-03, WP-LG-01; the Pack Studio service (no WP id).
- **States:** empty: nothing changed, so nothing to sign. loading: signing in progress on the button. error: a failing test blocks signing; the signature failed (nothing saved). live: tests re-run once more before signing. decided: signed, with the hash and a link to its ledger entry.
- **Milestone:** M2. **Demo step:** 6 (the new version is signed into the ledger). **Tablet:** no.

### Pack Studio v2 and Skill Studio (later)

- **Pack Studio v2** (`/studio/[packId]/documents`, `/workflows`, `/templates`): mark fields on a sample document with the evidence viewer, edit workflows, and edit deliverable templates. Phase 3. Depends on WP-RD-01, WP-RT-03, WP-DL-01.
- **Skill Studio** (`/studio/skills`): an organisation's experts write skills in the open format. Phase 3, part of WP-SK-05.

## Skills

### `/admin/skills`: Skills

- **Purpose:** install a skill from a folder or a zip, see what it may do in plain words, try it as a draft, and approve it for the organisation or for chosen groups (§7.27).
- **People:** Admin and Skill Approver; the person who installed a draft also sees it. **Run roles:** Analyst and Author (the personas a skill guides).
- **Components:**
  - `DataTable`: skill (the `skill` glyph), source (built-in, pack, organisation, third-party), version, status (draft, approved, disabled), approved for, permissions summary
  - an install flow that shows each step with its result: validate, scan, permissions, dependencies, try as draft, approve, record; anything flagged by the scan goes to the reviewer
  - approve, disable and uninstall; two approvers where the skill asks for tier-3 packs, scripts or network access
- **Data:** installed skills with status, version hash and permissions; scan findings; test results; approvals.
- **Depends on:** WP-SK-01, WP-SK-02, WP-SK-04, WP-LG-01. This page is WP-SK-05.
- **States:**
  - empty: only the built-in skills; one action: Install a skill.
  - loading: skeleton rows.
  - error: a skill refused at validation or scan, with the step and the finding; an approval refused for a missing second approver.
  - live: an install running through its steps, one step working at a time.
  - decided: approved skills, each with its ledger entry; disabled skills take effect at once.
- **Milestone:** M2. **Demo step:** —. **Tablet:** no.

### `/admin/skills/[skillId]`: Skill detail

- **Purpose:** everything about one skill before anyone approves it: its instructions, permissions, findings, tests and versions.
- **People:** Admin, Skill Approver. **Run roles:** Analyst, Author.
- **Components:** the skill's `SKILL.md` rendered as untrusted content (markdown, then sanitised); permissions in plain words; scan findings; tests with results; versions with hashes and permission diffs (later); ledger entries.
- **Data:** the skill's files, permissions, findings, tests, versions and ledger entries.
- **Depends on:** WP-SK-02, WP-SK-04.
- **States:** empty: n/a. loading: skeletons. error: failed to load. live: tests running. decided: the approved version, read-only.
- **Milestone:** M2; permission diffs on update and usage signals later (Phase 3). **Demo step:** —. **Tablet:** no.

## Admin

The admin area shares one sub-navigation: Users, Skills, Notices, and (later) Views, Policies and Connectors, plus a link to `/ops`. Each item shows only to roles that may open it.

### `/admin/users`: Users and roles

- **Purpose:** create local users, lock and unlock them, reset passwords, and give them access roles and groups.
- **People:** Admin. **Run roles:** none.
- **Components:** `DataTable` of users (name, access roles, groups, last sign-in, locked); a user dialog; a read-only tab showing how each active pack's role names map onto the core roles (for example `<Gate role>` → Reviewer, §7.3).
- **Data:** users, groups and roles; each pack's role mapping.
- **Depends on:** WP-ID-01, WP-ID-02, WP-PK-02.
- **States:** empty: only the first admin; one action: Add user. loading: skeleton rows. error: a duplicate username; removing the last admin refused. live: n/a. decided: every change is a `config.change` ledger entry.
- **Milestone:** M2 (M1 runs on seeded users; the demo needs a second person for maker-checker). **Demo step:** precondition for 3 and 4. **Tablet:** no.

### `/admin/notices`: Third-party notices

- **Purpose:** list every bundled component with its version, licence and where to get its source, as §2.7 requires.
- **People:** Admin; readable by anyone signed in (see the open questions). **Run roles:** none.
- **Components:** `DataTable`: component, version, licence, how it is used (imported, or a separate unmodified service), source location; each row expands to the licence and notice text in Plex Mono. Covers the bundled services, the frontend's own packages, fonts and icons.
- **Data:** the third-party bundle (`deploy/third-party/`) and the SBOMs, served as one list.
- **Depends on:** WP-F-02, WP-F-10.
- **States:** empty: n/a; a build without notices must fail CI, not show an empty page. loading: skeleton rows. error: the list failed to load. live: n/a. decided: n/a; the list changes only with a release.
- **Milestone:** M2, because the pitch build installs on other people's laptops (§11.2) and that is distribution. **Demo step:** —. **Tablet:** no.

### Later admin screens

- **`/admin/views`: Business views.** Runs by outcome, verification failure and catch rates, and approval latency, filterable by pack (§7.23). Uses the `figure` type step for KPI numbers. Phase 3. Depends on WP-RT-01, WP-RT-06, WP-SO-01. States: empty (no runs in the period), loading, error, live (n/a), decided (n/a).
- **`/admin/policies`: Policies.** Read and tighten the organisation's policies; a pack's defaults can be tightened but never loosened (§4.5, §7.4). Phase 3, with the policy engine (no WP id).
- **`/admin/connectors`: Data and cloud connectors.** Read-only data connectors (Phase 3, §7.18) and cloud model connectors (Phase 4, §7.22). Enabling one names the classifications allowed and the firewall exception, and it then shows in amber on the Sovereignty page.
- **`/ops`: Operations dashboards.** Grafana through the 4CE login (WP-OB-01); a link only, at M1.

## Proposed work packages

**What the plan's packages already cover:**

| WP       | Covers here                                                                                             |
| -------- | ------------------------------------------------------------------------------------------------------- |
| WP-F-09  | App shell, command palette, shortcut sheet, `/ui` and `/ui/motion` (assumed: "base components")         |
| WP-UI-01 | `/`, `/chat/[chatId]`, `/runs/[runId]` with the stage rail and status line, `/cases`, `/cases/[caseId]` |
| WP-UI-02 | The sign-off panel's fail-closed release (M1)                                                           |
| WP-UI-03 | Receipt, provenance, checks, revision cards, file cards for deliverables, `/runs/[runId]/audit`         |
| WP-UI-04 | `/sovereignty` and the sovereignty view                                                                 |
| WP-SK-05 | `/admin/skills`, `/admin/skills/[skillId]` (M2) and Skill Studio (later); no new id is proposed         |
| WP-OB-01 | `/ops`                                                                                                  |

The new packages follow, in the §12 table format. Each is written in the §12 template before it starts. Where a dependency is backend work with no WP id in §12, it is named by section; those are listed for R1 in the open questions.

**For M1:**

| WP       | Title                                                                                                                                                                        | Depends on                         |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| WP-UI-05 | Typed API client generated from the OpenAPI document, fake API (MSW) with sector-neutral fixtures, and the live-event client (one WebSocket, resume after the last sequence) | F-01; RT-01 for the event contract |
| WP-UI-06 | Sign-in, session expiry, no-access and error pages                                                                                                                           | F-09, ID-01, ID-02, UI-05          |
| WP-UI-07 | Evidence review: page image with numbered observation boxes, confidence and "check", verify and correct, capture on tablets                                                  | UI-01, RD-01, DM-01, PK-04, LG-01  |
| WP-UI-08 | Assessment and calculations: verdicts with clauses and pack hashes, calculation steps with units, authority results                                                          | UI-01, RL-01, CA-01, RT-04         |
| WP-UI-09 | Knowledge: collections, upload with file cards, ingest status                                                                                                                | UI-05, KN-01, KN-02, KN-03         |

**For M2:**

| WP       | Title                                                                                           | Depends on                                                                  |
| -------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| WP-UI-10 | Approval queue; maker-checker, two-person and authority states in the sign-off panel            | UI-02, SO-01, ID-02, policy engine (§7.4)                                   |
| WP-UI-11 | Verification page opened from a deliverable's QR code                                           | UI-03, LG-01, LG-02, RT-07, QR codes (§7.16)                                |
| WP-UI-12 | Ledger explorer and evidence-pack export                                                        | UI-05, LG-01, LG-02, evidence pack (§7.16)                                  |
| WP-UI-13 | Pack registry (list and activate), pack detail, and the live pack switcher                      | UI-01, PK-01, PK-02, PK-03, PK-04, RT-02                                    |
| WP-UI-14 | Pack Studio v1: vocabulary, rules, calculators and tests, with live test runs and a signed save | UI-13, PK-01, PK-03, PK-04, RL-01, CA-01, LG-01, Pack Studio service (§7.1) |
| WP-UI-15 | Users and roles admin, with each pack's role mapping                                            | F-09, ID-01, ID-02, PK-02                                                   |
| WP-UI-16 | Third-party notices page                                                                        | F-09, F-02, F-10                                                            |
| WP-UI-17 | Classification: levels on collections and documents, banners on runs, receipts and prints       | UI-09, UI-03, classification (§7.5)                                         |

**Later:**

| WP       | Title                                                             | Depends on                        |
| -------- | ----------------------------------------------------------------- | --------------------------------- |
| WP-UI-18 | Approval delegation with expiry; re-authentication when approving | UI-10, SO-01                      |
| WP-UI-19 | Business views by pack                                            | UI-15, RT-01, RT-06, SO-01        |
| WP-UI-20 | Policy admin                                                      | UI-15, policy engine (§7.4)       |
| WP-UI-21 | Install a pack from a bundle; upgrade with test replay            | UI-13, PK-02, PK-03               |
| WP-UI-22 | Pack Studio v2: document kinds, workflows, templates              | UI-14, UI-07, RD-01, RT-03, DL-01 |
| WP-UI-23 | Signed ledger checkpoints: list and print                         | UI-12, LG-02                      |
| WP-UI-24 | Data and cloud connectors, shown on the Sovereignty page          | UI-04, connectors (§7.18, §7.22)  |
| WP-UI-25 | Document detail with Deep Cache representations                   | UI-09, Deep Cache (§7.7)          |
| WP-UI-26 | Trends over a case's history                                      | UI-08, trend rules (§7.9)         |

## Build order

Every screen is built against the fake API first and switched to the real endpoint when its backend package lands (ADR-0035 §4). The order puts the shared pieces and the highest risk first, then follows the demo.

**Before anything here:** step 1 of the frontend plan, WP-F-09: tokens, base components, icons, the theme, motion and density modules, translations, and `/ui`.

**Towards M1:**

1. **WP-UI-05, the API and event client.** The typed client, the MSW fixtures, and a scripted run replayed as live events at real pace, including a dropped connection, a Challenger FAIL with a replan, and a stop. Everything below builds on it.
2. **The stage rail, node glyph and status line (WP-UI-01).** The signature component and the biggest design risk. Its motions are previewed on `/ui/motion` before the run view is built.
3. **Shell and sign-in (WP-F-09, WP-UI-06).** The frame every other screen sits in.
4. **Chat and the run view (WP-UI-01),** with file cards, citations and the run error card.
5. **The fail-closed path:** the sign-off panel (WP-UI-02), then the receipt, revision cards and audit sheet (WP-UI-03). After this an assured run goes end to end against the fake API.
6. **Evidence review and assessment (WP-UI-07, WP-UI-08).**
7. **Cases (WP-UI-01).**
8. **Sovereignty (WP-UI-04).** The pitch demo test starts here with step 1 and grows one step at a time (ADR-0035 §13).
9. **Knowledge (WP-UI-09).**

**Towards M2:**

10. **The pack switcher and registry (WP-UI-13) first,** because swapping vocabulary across every screen built so far finds any label that was not taken from the pack.
11. **The second person:** users (WP-UI-15), then the approval queue and the panel's maker-checker, two-person and authority states (WP-UI-10).
12. **Proof:** the ledger and evidence-pack export (WP-UI-12), then the verification page (WP-UI-11).
13. **Pack Studio v1 (WP-UI-14).**
14. **Classification (WP-UI-17), skills (WP-SK-05) and notices (WP-UI-16).**
15. **The full pitch demo as a browser test,** first against the fake API, then against the real server, with snapshots in light, dark, reduced motion, Hindi and print.

## Open questions

For R1 unless marked otherwise. This page states its assumption for each; changing one changes the screens named.

1. **Switching the pack (demo step 3).** "Switch the pack" could mean changing a person's working pack (no ledger entry) or activating a pack for the organisation (`pack.activate`). This page assumes the first in the shell and the second on `/packs`.
2. **Maker-checker timing.** §4.5 makes maker-checker always-on for tier-3 packs, and Phase 2 brings the policy engine and risk tiers, but §11.2 lists maker-checker in Phase 3. This page puts the panel's maker-checker states at M2, because demo steps 3 and 4 need a second person.
3. **Pack registry timing.** §11.2 puts the registry page in Phase 3, but demo step 3 needs a switch at M2. This page plans a reduced registry at M2 (list, activate) and install and upgrade later.
4. **Verification page access and size.** Should `/verify` work signed out? This page proposes that signed out shows only the result, ledger position, release time and chain status, with names and content after sign-in. Phones are later (ADR-0035 §6), yet a QR code is usually scanned with a phone: decide whether `/verify` gets a phone layout for M2.
5. **Fixture data (frontend owner).** ADR-0035 §4 says fixtures use the packs' synthetic demo data, while the neutrality check covers `apps/` (WP-F-04). This page assumes fixtures in `apps/web` stay neutral and pack-flavoured data reaches the browser only from the server.
6. **Rail nodes (frontend owner).** The rail is labelled with the six run roles, but the default workflow (§7.11) also has deterministic, execute and release stages with no role. How those appear is settled on `/ui/motion` before the rail is built.
7. **Backend work without a WP id in §12** that M2 screens depend on: the policy engine (§7.4), classification (§7.5), QR codes and the evidence-pack export with its verifier (§7.16), the Pack Studio service (§7.1), the Phase 2 rule types (§7.9), verification layers 2–4 (§7.14) and Deep Cache (§7.7).
8. **Splitting WP-SK-05.** It bundles the Skills page (Phase 2) with Skill Studio, permission diffs and usage signals (Phase 3). Splitting it lets the M2 part close.
9. **Knowledge at M1.** Assumed needed because chat answers cite documents; confirm against today's demo script.
10. **The pack approver's signature.** Proposed to use the sign-off panel's typed `approve`; confirm.
11. **`/ui` in the appliance build (frontend owner).** Ship it, or strip it from production builds.
12. **Who may read the notices.** §2.7 puts the page in the admin; this page proposes that anyone signed in can read it.
