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
| `make_s3_client(endpoint, *, access_key, secret_key, region, connect_timeout=5, read_timeout=60, attempts=3)` | The boto3 client for an S3 store: from a botocore session in which no `AWS_*` variable and no `~/.aws` file sets the endpoint, credentials, region, profile, proxy, CA bundle, retries, checksums, client-side monitoring, service data (`~/.aws/models`) or plugins. botocore 1.44.5 still adds a user-agent field and a trace header from the Lambda and execution variables, and loads `AWS_BEARER_TOKEN_S3` without using it to sign; `SSLKEYLOGFILE` makes urllib3 write TLS keys. The client is path-style, signs payloads with their SHA-256, asks for request checksums only where required, and by default waits 5 s to connect and 60 s to read and makes three attempts. Imported lazily: boto3 loads only for `FOURCE_STORAGE=s3`. The S3 stack's loggers stay at WARNING, because botocore prints request headers at DEBUG, and urllib3's at ERROR, because its warnings name the host; up to 40 pooled connections, one per worker thread |
| `S3Blobs(client, bucket, *, part_size=8 MiB, probe=None)` | Bytes as objects `<org hex>/<file hex>` in one bucket: one `put_object` up to a part, else a multipart upload holding one part in memory, aborted (shielded) on any failure or cancellation (a cancellation arriving during the final put or completion takes effect after it, so the new object may already be in place); reads stream and always close; a read of a key the store says is not there is `BlobMissing`, everything else (a write answered 404, a TLS failure part way through a body) `StorageUnavailable` with the S3 error code or the error's class logged, never botocore's text. `create_bucket()` makes the bucket only when it is missing, and a bucket another run created meanwhile is not an error (used by `fource-server migrate`). `ping()` asks `probe`, a client of its own (`open_storage` gives it one try, 2 s to connect and 2 s to read). Every call runs in a worker thread: a cancellation waits for the call in flight |
| `Storage(blobs, *, max_bytes)` | Files per organisation, in the caller's organisation session (the caller commits). `put(session, chunks, *, name, content_type, actor)` streams the bytes through a size cap and SHA-256, then adds the `stored_files` row and a `file.write` entry (hash, id, size, type; never the name). `stat(session, id)` and `open(session, id)` find the row in the session's organisation first (`FileNotFound` otherwise) |
| `FileInfo` | What 4CE knows about a file: id, name (for people only), type, size, SHA-256, when and by whom |
| `Reading` | A file being read: `.file`, then its bytes; at the end their size and SHA-256 are checked (`FileDamaged`) |
| `open_storage(settings)` | The `Storage` that `FOURCE_STORAGE` names, with `FOURCE_STORAGE_MAX_FILE_MB` |

## Tests

```
uv run pytest core/storage -m "not minio"
```

`just test-minio` runs the contract on a MinIO named by `FOURCE_TEST_S3_ENDPOINT`, `FOURCE_TEST_S3_ACCESS_KEY` and `FOURCE_TEST_S3_SECRET_KEY` (environment only; CI's MinIO job, or a throwaway container).

## Known limits

- The private-folder check on Linux and macOS reads the system's accounts with `pwd.getpwall()` to find accounts whose primary group is the store's group (a group lists only its supplementary members). Accounts that come from a directory service such as LDAP may not be listed there, so the check cannot see them; keep the store's folders closed to every account but 4CE's (for example `chmod 700`) on such a machine.
