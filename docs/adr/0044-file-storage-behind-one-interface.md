---
title: "File storage behind one interface"
type: adr
status: planned
owner: R1
updated: 2026-11-14
covers: []
tags: [4ce, adr]
number: 44
decision_status: proposed
superseded_by: null
---

# ADR-0044: File storage behind one interface

## Context

Master plan §6.3 puts originals, page renders, deliverables, pack bundles and index snapshots in MinIO, an unmodified separate service (§2.7), behind 4CE's own storage interface reached with boto3, with a local-filesystem adapter for development. §6.1 wants adapters at every third-party edge, no new outbound path and the hashes of every step in the ledger; §8.2 rule 10 wants organisation boundaries in every store, files included. The ledger is insert-only (§8.2 rule 8), so deleting a file must not touch it. Which service and which patch source run in a pilot is ADR-0025's open question (reserved); this record is about 4CE's side of the interface.

## Decision

1. **A `core/storage` package** owns the interface, two adapters and the metadata. In the layers contract it sits under `fource.server`, beside `fource.models` (neither imports the other), above `fource.identity`.
2. **Two adapters behind one protocol (`Blobs`):** `LocalBlobs` under `<FOURCE_DATA_DIR>/files`, and `S3Blobs` for MinIO or any S3-compatible store. `FOURCE_STORAGE` chooses (`local` by default, or `s3`); the existing `FOURCE_S3_*` settings configure the second.
3. **boto3, configured so that nothing outside 4CE's settings can steer it.** Each `S3Blobs` has one client from a botocore session whose configuration reads no environment variable and no file: no profile, no `~/.aws` files, no data path, no service data but botocore's own (none from `~/.aws/models`), no client plugin named by the environment, no client-side monitoring. The client gets the endpoint, access key, secret key and region explicitly, verifies TLS with the default trust store, uses no proxy, ignores configured endpoint URLs, path-style addressing, connect and read timeouts, and at most three attempts. Only `fource.storage` imports boto3, and only when `FOURCE_STORAGE=s3`.
4. **Keys are ids:** `<organisation uuid>/<file uuid>`, in lower-case hex. Adapters accept only a key of two UUIDs; a person's file name is metadata, never part of a path.
5. **Metadata lives in a `stored_files` table** per organisation under row-level security: name, type, size, SHA-256, who wrote it, and when it was deleted and erased. The app role may read, add and change rows, never delete them. Every read and delete finds the row in the caller's organisation session first.
6. **Writing:** the bytes stream through a meter (the size limit `FOURCE_STORAGE_MAX_FILE_MB`, the SHA-256) into the adapter; then the row and a `file.write` entry (the content's hash, the file id, size and type) are added in the caller's transaction. A rolled-back caller leaves an unreferenced blob, which nothing can read.
7. **Atomic writes:** a local file is written as a hidden part file (exclusive, owner-only on Linux and macOS; on Windows it takes the data folder's permissions), synced and renamed into place. The root is created owner-only. On Linux and macOS the store refuses a store or organisation folder that an account other than 4CE's or root owns or may write to (group write is allowed only for the owner's own private group, as on Debian and Ubuntu with umask 002), and a folder above the store that such an account owns or that others may write to unless it is sticky (like `/tmp`), as ssh does with `~/.ssh`; owners and permission bits decide, not access control lists. On Windows it relies on the data folder's ACLs, which must stay private; an organisation folder that is a link or junction is refused, and files are opened with `O_NOFOLLOW` where the system has it. S3 gets one `put_object` up to 8 MiB and, above it, 4CE's own multipart loop holding one 8 MiB part in memory at a time, aborted on any failure or cancellation. Every PUT and part carries a signed SHA-256 of its body, so the server refuses a damaged transfer.
8. **Blocking calls run in worker threads.** A cancellation waits for the call in flight (bounded by its timeouts), then takes effect; the cleanup that follows (closing a body, aborting an upload) runs shielded.
9. **Reading** streams the bytes and checks size and SHA-256 against the row at the end; a mismatch or missing bytes raise `file_damaged`.
10. **Deleting keeps the record and erases the bytes:** the row is marked deleted, a `file.delete` entry is written and a `storage.erase` job is queued, all in one transaction; reads refuse the file at once and the worker deletes the bytes and marks the row erased. The ledger holds only hashes, so erasure never touches it. Erasing writes no entry of its own: the record's `erased_at` is its evidence (decided by the project lead on 2026-11-02; an exception to ADR-0039's rule that every action writes an entry).
11. **The S3 bucket is created by `fource-server migrate`** when it is missing, never by the server at start-up: a misspelt bucket name must not silently start an empty store.
12. **Errors** are `storage_unavailable` (503), `file_not_found` (404), `file_too_large` (413) and `file_damaged` (500). No message, log line or entry carries an endpoint, a key, a path, a file name, content or a client library's own error text; the S3 stack's loggers stay above debug level, where botocore would print request headers, and urllib3's above warning level, where it names the host or a URL.

## Alternatives considered

| Option | Why not |
| --- | --- |
| 4CE's own Signature Version 4 signing on httpx | No new dependency and no threads, but 4CE would own a security-critical signer and every S3 call shape; the master plan names boto3, and the project lead chose it |
| A boto3 session as it comes | It reads `AWS_*` variables and `~/.aws`: an unknown profile stops it, client-side monitoring sends a datagram for every call to a host the environment names, and a configured endpoint or CA bundle could apply |
| boto3's `upload_fileobj` and transfer manager | They read ahead into buffers and threads of their own, with their own part sizes and retries; 4CE needs one part in memory and an abort it controls |
| An S3 client library with async support | Pins botocore and brings an HTTP stack of its own |
| Storing only blobs, with ids kept by each caller | No organisation check before a read, no hash to verify against, and every caller would repeat both |
| Deleting the row with the bytes | Loses the record that the file existed; the bytes could go while a row still pointed at them if the caller rolled back |
| Creating the bucket at server start | Hides a misconfiguration behind an empty store |

## Consequences

- Each package that keeps files (knowledge, deliverables, the sandbox) calls `Storage` and gets organisation scoping, integrity and ledger entries without repeating them.
- MinIO's patch source (ADR-0025) can change, or MinIO can be replaced by another S3-compatible store, with a configuration change.
- New runtime dependencies, for `FOURCE_STORAGE=s3` only at run time but installed everywhere: boto3, botocore and s3transfer (Apache-2.0), jmespath, six and urllib3 (MIT), python-dateutil (Apache-2.0 and BSD-3-Clause); type stubs for development only (MIT).
- CI gains a `minio` job that builds the image compose uses and runs `just test-minio`: the blob contract, multipart uploads and a body changed after signing refused, on real MinIO (the one CI change of WP-F-08, approved by the project lead on 2026-11-02).
- Known limits: unreferenced blobs from rolled-back callers are not swept yet; per-purpose MinIO keys and bucket policies are a WP-F-10 follow-up (development uses the root credentials); files belong to one organisation, so installation-wide files (pack bundles) need a later decision.

## Status

Proposed on 2026-11-01 for WP-F-08, revised 2026-11-02 (boto3, decided by the project lead) and 2026-11-08 (point 7's folder rule: the store refuses a store or organisation folder, or one above it, that another account can use to reach the files; confirmed by the project lead on 2026-11-11). To be confirmed by R1 and R4.
