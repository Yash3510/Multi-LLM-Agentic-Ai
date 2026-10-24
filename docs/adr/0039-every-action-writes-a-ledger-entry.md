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
| `identity.signin.failure` | `anonymous` | `reason` (`unknown_email`, `inactive`, `wrong_password`, `locked`); `user` when the email is known; for an unknown email, `inputs_sha256` = HMAC-SHA256 of the trimmed, lower-cased address (see point 5) |
| `identity.lockout` | `system` | `user`, `until` |
| `identity.signout` | `user:<id>` | `user`, `token` |

5. **No email address is stored.** The ledger can never be erased, so it holds ids; an unknown address is kept only as a keyed hash, decided by the project lead on 2026-10-24. A plain SHA-256 would let anyone with the ledger find a common address by guessing and hashing. The key is derived from the installation secret (`HMAC-SHA256(FOURCE_SECRET_KEY, "4ce-ledger-unknown-email-v1")`), never the secret itself, so someone holding the secret can confirm an address and someone with only the ledger or an evidence pack cannot.
6. Each later work package adds its own types to `EntryType` and records new groups in an ADR.

## Alternatives considered

| Option | Why not |
| --- | --- |
| The server writes entries around each route | Entries would live in a different transaction from the action, and actions called from commands (create-user) would be missed |
| A plain SHA-256 of an unknown email | A common address can be found by guessing and hashing, by anyone who has the ledger |
| Store the email of failed sign-ins | Personal data of people who may not be users, in a store that can't be erased |
| Record nothing for unknown emails | Loses the trail of guessing attacks; the keyed hash keeps it without the address (confirmed by the project lead on 2026-10-24) |

## Consequences

- Every failed sign-in now writes and commits a row, also for unknown emails; this evens out timing rather than adding a difference.
- Rotating `FOURCE_SECRET_KEY` means unknown-email digests written earlier can no longer be confirmed; the entries stay and the chain still verifies.
- The token id in sign-in and sign-out entries links a session's start and end.

## Status

Proposed on 2026-10-24, decided by the project lead. To be accepted by R1.
