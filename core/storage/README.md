# fource-storage

Files per organisation (master plan §6.3, §7.24): the storage interface, a local-filesystem adapter and an S3 adapter for MinIO, and the `stored_files` records that every read and delete goes through. Keys are ids, never names; every write is hashed and recorded in the ledger; deleting keeps the record and erases the bytes.

**Owner:** R1 · **Decisions:** [ADR-0041](../../docs/adr/0041-file-storage-behind-one-interface.md)

## Public API

| Name | What it is |
| --- | --- |
| `BlobKey(org, file)` | Where one file's bytes live: two UUIDs; `.path` is `<org hex>/<file hex>` |
| `StoredFile` | The `stored_files` table: name, type, size, SHA-256, who wrote it, and when it was deleted and erased. Rows are never deleted |
| `StorageUnavailable`, `FileNotFound`, `FileTooLarge`, `FileDamaged` | The errors callers see (503, 404, 413, 500); messages never carry an endpoint, key, path or content |
| `BlobMissing` | What an adapter raises when a key has no bytes |

## Tests

```
uv run pytest core/storage
```
