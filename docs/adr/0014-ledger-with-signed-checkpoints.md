---
title: "Ledger with signed checkpoints"
type: adr
status: planned
owner: R1
updated: 2026-10-25
covers: []
tags: [4ce, adr]
number: 14
decision_status: proposed
superseded_by: null
---

# ADR-0014: Ledger with signed checkpoints

## Context

Master plan §7.16 asks for an insert-only, hash-chained evidence ledger on PostgreSQL, with Ed25519-signed checkpoints of the chain head, and detection of edits, deletions, reordering and truncation. Appendix B fixes the entry's fields. 4CE runs on SQLite in development and PostgreSQL 18 in production ([ADR-0010](0010-modular-monolith-on-one-database.md)), and every table is confined to one organisation (§7.24).

## Decision

1. **A `core/ledger` package** owns the ledger. It sits below `core/identity` and above `core/db` in the layers contract, so any package can append on its own session.
2. **One chain per organisation.** `ledger_entries` is organisation-scoped and under row-level security like every other table; each organisation's entries count from 1. The entry's `org` (the organisation's id) is part of the hash.
3. **Entries hold hashes and ids, never content:** `seq`, `at`, `org`, `run`, `case`, `type`, `actor`, `inputs_sha256`, `outputs_sha256`, `refs` (an object of short strings), `prev`, `hash`.
4. **The hash** is SHA-256, in hex, of the entry's fields without `hash`, serialised as JSON with sorted keys, no spaces and UTF-8 text (`json.dumps(…, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). For 4CE's value types this equals RFC 8785. `at` is UTC with milliseconds and a `Z`. The first entry's `prev` is 64 zeros. A fixed test vector pins the format.
5. **Numbers are taken under a lock.** A head row per organisation (`ledger_heads`) is written first (`INSERT … ON CONFLICT DO NOTHING`, then `UPDATE … SET seq = seq + 1 RETURNING`), so the row (PostgreSQL) or the database (SQLite) stays locked until the transaction ends. Entries never share or skip a number, and a rolled-back action takes its number back.
6. **Insert-only, on both engines.** Triggers refuse UPDATE and DELETE (and TRUNCATE on PostgreSQL) with "ledger_entries is insert-only"; the app role is granted only SELECT and INSERT on the entries.
7. **Signed checkpoints.** `fource-server ledger checkpoint` signs `{org, seq, hash, at, key}` of the head, prefixed with `4ce-ledger-checkpoint-v1\n`, with the installation's Ed25519 key; records the signature as the next entry (type `checkpoint`); and writes the same checkpoint to a file a person keeps off the machine.
8. **The key** is a PEM file at `FOURCE_LEDGER_KEY_FILE` (default inside the git-ignored `data/`), created owner-only by `fource-server ledger keygen`, never overwritten, never printed. Its id is the SHA-256 of the raw public key. People sign checkpoints with `fource-server ledger checkpoint`; a scheduled job may sign them too, once the job queue lands (WP-F-07), decided by the project lead on 2026-10-24. Nothing in CI or the tests signs with a real installation key.
9. **The verifier** (`fource-server ledger verify`) recomputes every hash and link, checks checkpoint entries and outside checkpoint files against the public key, and reports problems by kind. It is a pure function over entries, the public key and checkpoints (standard library and `cryptography` only), so it can later run with no database. Without the public key, signatures count as unchecked, never valid, and the command exits 2, not 0.

## Alternatives considered

| Option | Why not |
| --- | --- |
| One global chain | Every organisation's writes would contend for one lock, row-level security would hide links from each organisation, and one organisation's evidence couldn't be verified without another's entries |
| `MAX(seq)` read, or PostgreSQL advisory locks | The read races on SQLite; advisory locks exist only on PostgreSQL |
| A separate checkpoints table | Whoever can cut the tail can cut that table too; only a copy outside the database proves the length. The `checkpoint` entry already records that signing happened |
| Storing content in entries | Secrets and document content never enter the ledger (§8.2 rule 8) |

## Consequences

- A truncated tail, or a chain rewritten from the start with fresh hashes, is detected only against a signed checkpoint kept outside the database. Between checkpoints, the table owner (who can disable triggers) or a superuser could cut the newest entries unseen.
- A migration that rebuilds `ledger_entries` on SQLite (batch mode) must recreate its triggers.
- Key rotation and scheduled checkpoints are future work; scheduled checkpoints wait for the job queue (WP-F-07).
- QR codes, evidence packs and the auditor's standalone script build on the verifier in later work packages.

## Status

Proposed on 2026-10-24, decided by the project lead ("build everything according to the master plan"). To be accepted by R1.
