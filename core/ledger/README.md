# fource-ledger

The evidence ledger (master plan §7.16): one insert-only, hash-chained list of entries per organisation, signed checkpoints of the chain head, and the verifier. Entries hold hashes and ids, never content.

**Owner:** R1 · **Decisions:** [ADR-0014](../../docs/adr/0014-ledger-with-signed-checkpoints.md), [ADR-0039](../../docs/adr/0039-every-action-writes-a-ledger-entry.md)

`chain.py`, `checkpoints.py` and `verify.py` use only the standard library and `cryptography`, so the verifier can later run without a database.

## Public API

| Name | What it is |
| --- | --- |
| `Entry`, `EntryType` | One entry, field for field as Appendix B shows it, and every type 4CE writes |
| `make_entry(...)` | A checked entry with its hash; `ValueError` for anything malformed |
| `canonical(value)`, `entry_hash(fields)`, `sha256_hex(data)` | The byte form that is hashed and signed (sorted-key JSON, no spaces, UTF-8), and SHA-256 in hex |
| `format_time(dt)`, `to_millis(dt)` | Entry times: UTC, whole milliseconds, `2026-11-14T10:22:31.512Z` |
| `GENESIS`, `SYSTEM`, `ANONYMOUS`, `user_actor(id)` | The first entry's `prev`, and the three kinds of actor |

## Tests

