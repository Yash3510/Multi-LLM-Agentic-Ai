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
| `Checkpoint`, `sign_checkpoint(key, org=, seq=, hash=, at=)`, `is_signed_by(checkpoint, public_key)` | A signed chain head: Ed25519 over `4ce-ledger-checkpoint-v1\n` + the canonical `{org, seq, hash, at, key}`; `key` is `key_id(public_key)`, the SHA-256 of the raw public key. `Checkpoint.from_dict` reads one back from a file |
| `write_key_pair(key, path)`, `load_private_key(path)`, `load_public_key(path)`, `public_key_path(path)` | The installation key as PEM files: the private key owner-only and never overwritten, the public key beside it (`signing-key.pem` -> `signing-key.pub.pem`) |
| `verify_chain(entries, org, public_key=, checkpoints=)`, `ChainVerifier`, `Verification`, `Problem` | Checks a chain entry by entry (streamable): hashes, links, numbering, organisation, checkpoint entries, and outside checkpoints (truncation, rewrites). `Verification.ok` means no problems; `complete` also means every signature was checked. Without the public key nothing is anchored. A malformed entry is reported as a problem, never raised |

## Tests

