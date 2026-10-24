---
title: "Every action writes a ledger entry"
type: adr
status: planned
owner: R1
updated: 2026-10-24
covers: []
tags: [4ce, adr]
number: 39
decision_status: proposed
superseded_by: null
---

# ADR-0039: Every action writes a ledger entry

## Context

AGENTS.md §7: "Every new action writes a ledger entry." Master plan Appendix B lists entry types for runs, decisions, calls, evidence, sign-off, packs, skills and administration, but none for identity, and the actions built so far are all identity actions.

## Decision

1. **The entry is written in the action's own transaction,** on the same session: committed with the action, or not at all. An action that ends in an error the caller rolls back (a failed sign-in) commits its entry first.
2. **Identity entry types:** `identity.user.create`, `identity.signin.success`, `identity.signin.failure`, `identity.lockout`, `identity.signout`.
3. **Actors:** `system` (the server or an operator's command), `anonymous` (not signed in), `user:<id>`.
4. **What they record:**

| Type | Actor | Refs and hashes |
| --- | --- | --- |
| `identity.user.create` | `system` | `user`, `roles` |
| `identity.signin.success` | `user:<id>` | `user`, `token` (the token's id) |
| `identity.signin.failure` | `anonymous` | `reason` (`unknown_email`, `inactive`, `wrong_password`, `locked`); `user` when the email is known; for an unknown email, `inputs_sha256` = SHA-256 of the trimmed, lower-cased address |
| `identity.lockout` | `system` | `user`, `until` |
| `identity.signout` | `user:<id>` | `user`, `token` |

5. **No email address is stored.** The ledger can never be erased, so it holds ids; an unknown address is kept only as its hash, so an investigator who already has an address can confirm attempts without the ledger holding it.
6. Each later work package adds its own types to `EntryType` and records new groups in an ADR.

## Alternatives considered

| Option | Why not |
| --- | --- |
| The server writes entries around each route | Entries would live in a different transaction from the action, and actions called from commands (create-user) would be missed |
| Store the email of failed sign-ins | Personal data of people who may not be users, in a store that can't be erased |
| Record nothing for unknown emails | Loses the trail of guessing attacks; the hash keeps it without the address (to be confirmed by the project lead) |

## Consequences

- Every failed sign-in now writes and commits a row, also for unknown emails; this evens out timing rather than adding a difference.
- The token id in sign-in and sign-out entries links a session's start and end.

## Status

Proposed on 2026-10-24, decided by the project lead. To be accepted by R1.
