# fource-storage

Files per organisation (master plan §6.3, §7.24): the storage interface, a local-filesystem adapter and an S3 adapter for MinIO, and the `stored_files` records that every read and delete goes through. Keys are ids, never names; every write is hashed and recorded in the ledger; deleting keeps the record and erases the bytes.

**Owner:** R1 · **Decisions:** [ADR-0044](../../docs/adr/0044-file-storage-behind-one-interface.md)

## Public API

| Name | What it is |
| --- | --- |
| `BlobKey(org, file)` | Where one file's bytes live: two UUIDs; `.path` is `<org hex>/<file hex>` |
| `StoredFile` | The `stored_files` table: name, type, size, SHA-256, who wrote it, and when it was deleted and erased. Rows are never deleted |
| `StorageUnavailable`, `FileNotFound`, `FileTooLarge`, `FileDamaged` | The errors callers see (503, 404, 413, 500); messages never carry an endpoint, key, path or content |
| `BlobMissing` | What an adapter raises when a key has no bytes |
| `Blobs` | The adapter protocol: `write(key, chunks)` stores every chunk or nothing, `read(key)` streams (async context manager; `BlobMissing` when absent), `delete(key)` may repeat, `ping()`, `close()` |
| `LocalBlobs(root)` | Bytes as files `<root>/<org hex>/<file hex>` (the server uses `<FOURCE_DATA_DIR>/files`): written to an exclusive part file (owner-only on Linux and macOS; on Windows the files take the data folder's permissions, so keep that folder private), synced and renamed into place; organisation folders and files that are links are refused; on Linux and macOS the store is used only when no other account can change its folders or a folder above them (ADR-0044, point 7); blocking calls run in worker threads |
| `CHUNK_SIZE` | 64 KiB, the size adapters read in |

## Tests

```
uv run pytest core/storage
```
