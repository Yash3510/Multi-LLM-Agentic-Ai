---
title: "ADR-0002: Human approval fails closed"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - security
---

# ADR-0002: Human approval fails closed

## Context

The approval gate is the one control that keeps a person in the loop. The
platform's yes/no confirm dialog treats a stray Enter as approval unless
focus happens to be on a link, button or text area, so an unreviewed
deliverable could be released by reflex (`aca731e`). An early build also
recorded "HUMAN approved" when no interactive session existed to ask anyone
(`c256b89`).

## Decision

The reviewer must type `approve`. Everything else withholds the result: an
empty box, another word, a cancel, a timeout, a closed tab. The record says
which of those happened:

| What happened | Recorded as | Released |
|---|---|---|
| `approve` or `approved` typed | approved, with time and reviewer | yes |
| Anything else | rejected | no |
| The prompt reached nobody, or timed out | not obtained | no |
| No interactive session at all | not obtained, unapproved | no |

The wait is finite: `WEBSOCKET_EVENT_CALLER_TIMEOUT=1800` in
[`env.sovereign.example`](../../env.sovereign.example). Unset, the platform
would wait forever, and "a timeout withholds" would never actually happen.

## Alternatives considered

- **The platform's confirm dialog.** Rejected for the Enter-key hazard above.
- **Hold to release**, pressing the button or Enter for about a second. It was
  built (`e8c8163`) and then reverted to the typed word (`f276768`). The
  review content around it stayed: the checks, the sources and what changed.

## Consequences

- Greetings must not reach the gate, or reviewers learn to approve anything.
  That is one reason for the fast path in
  [ADR-0008](0008-answer-conversation-directly.md).
- A reload during sign-off would lose the prompt, so a pending sign-off is
  re-sent to the same user's live sessions when the tab reconnects (`080bb60`).
- The reviewer's waiting time is excluded from the reported working time
  (`d7cfde5`).

## Status

Accepted, `aca731e` (2026-09-08). Refined in `c256b89`, `6ce13f3`, `080bb60`
and `f276768`.

## Related

- [AGENT_CHAIN.md - HUMAN](../AGENT_CHAIN.md#human---sign-off)
- [history/2026-09-08-visible-reasoning-and-approval-gate.md](../history/2026-09-08-visible-reasoning-and-approval-gate.md)
