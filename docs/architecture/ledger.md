---
title: "Ledger"
type: architecture
status: active
owner: R1
updated: 2026-10-25
covers:
  - core/ledger/
  - apps/server/src/fource/server/ledger_commands.py
tags: [4ce, architecture, ledger, security]
---

# Ledger

The evidence ledger records every action 4CE takes as a hash-chained, insert-only list of entries per organisation, so a later edit, deletion, reordering or cut can be detected. The code is [`core/ledger`](../../core/ledger/README.md); the three commands are in [`ledger_commands.py`](../../apps/server/src/fource/server/ledger_commands.py) and listed in the [API](api.md#running-it) page.

## Entries

Each organisation has its own chain, counting from 1. An entry holds hashes and ids, never content (master plan Appendix B):

| Field | What it holds |
| --- | --- |
| `seq` | Its number in the organisation's chain |
| `at` | UTC time with milliseconds: `2026-11-14T10:22:31.512Z` |
| `org` | The organisation's id |
| `run`, `case` | The run and case it belongs to, or null (runs and cases come later) |
| `type` | One of `EntryType`: `checkpoint`, and the five identity types of [ADR-0039](../adr/0039-every-action-writes-a-ledger-entry.md) |
| `actor` | `system`, `anonymous` or `user:<id>` |
| `inputs_sha256`, `outputs_sha256` | SHA-256 (64 hex digits) of what went in and came out, or null. Today only a failed sign-in with an unknown email sets one: a keyed hash, see [identity](identity.md#ledger) |
| `refs` | Short named strings (names in lower snake case, values printable text of up to 1000 characters): ids, reasons, times |
| `prev` | The previous entry's hash; 64 zeros for the first |
| `hash` | SHA-256 of all the fields above |

`make_entry` accepts exactly one form per value (lower-case UUIDs, the time format above, and so on) and raises `ValueError` for anything else, because a malformed entry is a bug in the code writing it.

**The hash** is SHA-256, in hex, of every field but `hash`, as JSON with sorted keys, no spaces and UTF-8 text. For seq 1, at `2026-11-14T10:22:31.512Z`, org `0192f5a0-0000-7000-8000-000000000001`, type `identity.user.create`, actor `system`, refs `{"user": "0192f5a0-0000-7000-8000-0000000000aa", "roles": "Admin"}`, everything else null and `prev` the 64 zeros, the hash is `29c04f35f9fa3620715310e44047300b908992276697f036c12778ffae208585` (pinned in `core/ledger/tests/test_chain.py`; rerun by hand when this page was written).

## Writing

`append(session, type, actor=, refs=, …)` writes in the caller's session, so the entry is committed with its action or not at all. It first writes the organisation's row in `ledger_heads` (insert if missing, then add one to `seq`), which locks that row on PostgreSQL and takes SQLite's write lock: parallel writers queue, and numbers are never shared or skipped. A rolled-back action takes its number back. The head row is not evidence and the verifier never reads it.

## Insert-only

- Triggers refuse UPDATE and DELETE on `ledger_entries` on both engines, and TRUNCATE on PostgreSQL ("ledger_entries is insert-only").
- On PostgreSQL the app role (`fource_app`) may only SELECT and INSERT entries, under row-level security like every table ([database](database.md#row-level-security)). The server also refuses to start as a role that bypasses row-level security.
- The table owner can still disable a trigger, and a superuser bypasses everything. Signed checkpoints kept outside the database are what detect that.

## Checkpoints and the key

- `just ledger keygen` creates the installation's Ed25519 key at `FOURCE_LEDGER_KEY_FILE` (default `data/ledger/signing-key.pem`, git-ignored), owner-only, with the public key beside it (`signing-key.pub.pem`). It never overwrites either file: if one exists it changes nothing and exits 1. Back the private key up; give the public key to auditors.
- `just ledger checkpoint [--org SLUG] [--out DIR]` signs the chain head, records the signature as the next entry (type `checkpoint`, actor `system`, refs `seq`, `hash`, `key`, `signature`), prints the checkpoint as JSON and writes it to `data/ledger/checkpoints/<org>-<seq>.json` (`seq` padded to ten digits, the entry that was signed). **Keep a copy off the machine** (print it, or put it on write-once storage): only an outside copy can prove how long the chain was.
- A checkpoint file is never overwritten. If the file exists, the checkpoint entry is still recorded, the JSON is printed, the existing file is left as it is and the command exits 1. The same applies when the file cannot be saved: keep the printed JSON.
- A checkpoint signs the bytes `4ce-ledger-checkpoint-v1\n` followed by the canonical `{org, seq, hash, at, key}`, where `key` is the SHA-256 of the raw public key.
- **Who signs.** People run `just ledger checkpoint`. A scheduled job may sign checkpoints too, once the job queue lands (WP-F-07); that is decided and not built ([ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md)). Nothing in CI or the tests signs with a real installation key; tests use throwaway keys.

## Verifying

`just ledger verify [--org SLUG] [--public-key FILE] [--checkpoints DIR]` reads the organisation's chain and every checkpoint file of that organisation in the folder (default `data/ledger/checkpoints`), uses the public key beside the private key unless `--public-key` is given, and reports each problem as `entry N: kind: message`:

| Problem | Means |
| --- | --- |
| `altered` | an entry's contents don't match its hash (or its number isn't a whole number) |
| `broken_link` | an entry doesn't link to the one before it |
| `missing` | numbers are skipped |
| `out_of_order` | numbers go backwards |
| `wrong_org` | an entry or checkpoint of another organisation |
| `bad_checkpoint` | a checkpoint, in an entry or a file, whose signature or references are wrong |
| `checkpoint_mismatch` | the chain differs from what a checkpoint signed (rewritten) |
| `truncated` | a checkpoint signed an entry that is gone (cut tail) |
| `unreadable` | the database could not return an entry or the ones after it, so they were not checked |

The exit code and the last line:

| Exit | Last line | Means |
| --- | --- | --- |
| 0 | `Verified.` | no problems, every signature checked |
| 0 | `Verified through entry N; entries after it are not covered by any checkpoint.` | the same, but entries after the last outside checkpoint can't be shown intact |
| 1 | `Failed.` | at least one problem found in the chain or the checkpoints |
| 1 | a message naming the path | a key, checkpoint folder or file that is missing or could not be read, or an organisation that doesn't exist; nothing is checked |
| 2 | `Incomplete: nothing wrong found, but not all checked.` | signatures couldn't be checked because there is no public key (the output names where it looked); never reported as verified |

Exit 0 is not proof of the chain's length: a cut-off tail is only visible against a checkpoint that was signed with the key and kept outside the database. So when no valid outside checkpoint anchors the chain, even a clean run prints "The chain's length is not proven …" before `Verified.`, and when entries follow the last anchor it says they are not covered and to make a new checkpoint. The newest checkpoint entry always follows the entry it signs; it alone is not counted as uncovered.

Anything that cannot be read is a failure (exit 1), never "no checkpoints": an explicit `--checkpoints` folder that doesn't exist, an unreadable or malformed checkpoint file, key file or folder, and a default folder that is a dangling link. Only a missing default folder means none. Rows changed in the database (any odd cell value) are reported as problems, never a crash.

The verifier (`chain.py`, `checkpoints.py`, `verify.py`) uses only the standard library and `cryptography`, and takes entries from anywhere, so it can later run on an auditor's machine without a database.

## Known limits

- **SQLite's `INSERT OR REPLACE`** gets past the insert-only triggers on the development engine. PostgreSQL has no REPLACE and the app role has no UPDATE.
- **The owner or a superuser between checkpoints:** they can disable a trigger and cut the newest entries unseen until the next outside checkpoint.
- **No key rotation yet.**
- **Scheduled checkpoints wait for the job queue** (WP-F-07).
- **A SQLite batch rebuild of `ledger_entries` must recreate its triggers** ([database](database.md#known-limits)).
- **PostgreSQL from a Windows host is untested** ([database](database.md#known-limits)).
- **Export, QR codes and evidence packs** are not built; they come with the release work packages.

## Decisions

[ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md) (the ledger) and [ADR-0039](../adr/0039-every-action-writes-a-ledger-entry.md) (every action writes an entry), both still proposed.

## Acceptance

Edits, deletions, reordering and, against a checkpoint, truncation are detected: `core/ledger/tests/test_verify.py` and `apps/server/tests/test_cli.py`. On PostgreSQL the ledger can't be changed or emptied by the app role: `apps/server/tests/test_postgres.py`, run in CI's PostgreSQL job.
