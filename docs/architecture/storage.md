---
title: File storage
type: architecture
status: active
owner: R1
updated: 2026-11-22
covers:
  - core/storage/
tags: [4ce, architecture, storage, security]
---

# File storage

How 4CE keeps files: originals, renders, deliverables, index snapshots. The code is [`core/storage`](../../core/storage/README.md); MinIO itself is on the [bundled services](services.md) page.

## Two stores, one interface

- **A local folder** (`FOURCE_STORAGE=local`, the default): `<FOURCE_DATA_DIR>/files`. For development and single-machine installs, like SQLite for the database.
- **An S3 bucket** (`FOURCE_STORAGE=s3`): MinIO, or any S3-compatible store.
- Both sit behind one protocol, `Blobs` (`write`, `read`, `delete`, `ping`, `close`), which knows nothing of records, sizes or hashes. [`Storage`](../../core/storage/README.md) adds those on top.

| Setting | Default | What it does |
| --- | --- | --- |
| `FOURCE_STORAGE` | `local` | `local` or `s3` |
| `FOURCE_STORAGE_MAX_FILE_MB` | 512 | The size of one file at most; 1 to 65536 |
| `FOURCE_S3_ENDPOINT` | unset | `http://` or `https://`, a host and an optional port, with no path, user, query or fragment; the host is letters, digits and hyphens between dots, or an IPv6 address. Needed with `s3` |
| `FOURCE_S3_ACCESS_KEY`, `FOURCE_S3_SECRET_KEY` | unset | The credentials. Needed with `s3`; the secret is never shown in a log or a repr |
| `FOURCE_S3_BUCKET` | `fource` | 3 to 63 lower-case letters, digits and hyphens, starting and ending with a letter or digit |
| `FOURCE_S3_REGION` | `us-east-1` | 1 to 32 lower-case letters, digits and hyphens, starting and ending with a letter or digit, not all digits |

`Settings` refuses `FOURCE_STORAGE=s3` when the endpoint or either key is missing or blank. `fource-server migrate` creates the bucket when `FOURCE_STORAGE=s3` and it is missing (`Created the bucket …` or `Found the bucket …`); the server never creates it, so a misspelt name can't start an empty store. `/api/health` reports `"storage": "ok"` or `"unavailable"` and answers 503 when it is unavailable ([API](api.md#endpoints)): the local store is `ok` when its folder exists (or can be made), is writable and, on Linux and macOS, no other account can change it ([Writing](#writing-reading-deleting)), the S3 store when a `HEAD` on the bucket succeeds.

## Keys, records and the ledger

- **A key is two ids:** `<organisation uuid>/<file uuid>`, in lower-case hex. `BlobKey` accepts nothing but two `uuid.UUID` values. A person's file name is only in the record, never in a path or key, so no name can reach outside its organisation's folder or prefix.
- **Every file has a record** in `stored_files` (migration `0006`, per organisation, under forced row-level security on PostgreSQL): name (1 to 255 printable characters), content type (a lower-case `type/subtype`), size, SHA-256, who wrote it, and when it was deleted and by whom and when it was erased. A size below 0 is refused by the check constraint `stored_files_size`. The app role may read, add and change records, never delete them: on PostgreSQL it has no `DELETE` grant, and on SQLite migration `0007` adds the trigger `stored_files_no_delete`, which refuses a `DELETE` ("stored_files rows are never deleted"). A name or type that breaks those rules raises `ValueError`: a caller's bug, not an API error.
- **Every read and delete finds the record in the caller's organisation session first**, with the organisation named in the query as well as in the session, so another organisation's id finds nothing (`file_not_found`).
- **Every write is in the ledger:** `file.write` with the content's plain SHA-256 as its output hash and the refs `file` (the id), `size` and `content_type`, in the caller's transaction; never the name. Deleting writes `file.delete` with the ref `file` ([ledger](ledger.md#entries)). Erasing the bytes writes no entry: the record's `erased_at` is its evidence ([ADR-0044](../adr/0044-file-storage-behind-one-interface.md), point 10).

## Writing, reading, deleting

- **Writing** streams the bytes through a meter (the size limit and the SHA-256) into the store; only then are the record and the entry added, in the caller's session. A file over the limit raises `file_too_large` ("A file may be at most 512 MiB (FOURCE_STORAGE_MAX_FILE_MB)."), and the adapter discards what it had. If the caller rolls back after `put` returns, the bytes stay in the store with no record: an unreferenced blob that nothing can read, and that nothing sweeps yet (ADR-0044, point 6).
  - **The local store** writes a hidden part file (created exclusively, owner-only on Linux and macOS; on Windows the files take the data folder's permissions, so keep the data folder private), syncs it and renames it into place, so a reader sees the whole file or none. It refuses an organisation folder that is a link or junction and opens files with `O_NOFOLLOW` where the system has it. On Linux and macOS it is used only when no other account can change its folders: the store's and the organisations' folders must be 4CE's account's (or root's) and closed to writes by others (group write only for the owner's private group), and every folder above them must be the account's or root's and, if others may write to it, sticky like `/tmp` (ADR-0044, point 7).
  - **The S3 store** sends one `put_object` for up to 8 MiB and, above that, a multipart upload in parts of 8 MiB. An upload holds about two parts in memory: the buffer and the copy being sent (a test pins it under two and a half parts). Any failure or cancellation aborts the upload. A cancellation that arrives during the final call (the `put_object` or the completion) takes effect after it, so the new object may already be in place when the write is cancelled.
- **Reading** streams the bytes through `Storage.open`, which gives a `Reading`. A `Reading` is read once: a second pass raises `RuntimeError`. It checks size and SHA-256 against the record: a stored blob longer than its record stops with `file_damaged` at the recorded size, and at the end a different size or hash raises `file_damaged` too, as do missing bytes. The chunks before the difference are already with the caller, so a caller that gets `file_damaged` treats the whole read as failed (a caller streaming to a client has already sent them).
- **Deleting** is one statement that marks the record (`deleted_at`, `deleted_by`) only if it is in the caller's organisation and not deleted yet, then the `file.delete` entry, then a `storage.erase` job (key `storage.erase:<file id>`, 30 attempts), all in the caller's transaction. Readers lose the file at once; of two deletes at once the second finds no file (`file_not_found`) and the deletion is recorded once; a rolled-back delete changes nothing.
- **Erasing** is the worker's `storage.erase` job ([jobs](jobs.md#the-worker-command)): it reads the record in the job's organisation, does nothing unless the file is deleted and not yet erased, deletes the bytes (a key with none is fine) and sets `erased_at`. A repeated job is harmless, and another organisation's id erases nothing. The ledger keeps only hashes, so erasing never touches it.

## The S3 client

`make_s3_client` is the only place that builds one, with boto3 and a botocore session whose configuration reads no `AWS_*` variable and no `~/.aws` file: no profile, no configuration or credentials file, no data path, no service data from `~/.aws/models` (only botocore's own, so no file there can change S3's endpoint rules), no client plugin named by `BOTOCORE_EXPERIMENTAL__PLUGINS`, no client-side monitoring (which would send a datagram per call to a host the environment names). It gets its endpoint, keys and region explicitly, checks TLS against certifi's bundle whatever `AWS_CA_BUNDLE` or `REQUESTS_CA_BUNDLE` say, uses no proxy (`proxies={}`; only `None` would fall back to the environment), addresses buckets by path, waits 5 s to connect and 60 s to read, and tries a request at most three times. Health's check uses a second client that tries once, with 2 s to connect and 2 s to read, so a stopped store shows `unavailable` within seconds instead of after three long attempts. A wrong-region answer is retried at the same host, with the region it names. Every PUT and part signs the SHA-256 of its body, and request checksums are added only where an operation requires one, so the server always checks the body it stored.

**The trust store.** `verify=True` checks TLS against **certifi's bundle**, which botocore loads when certifi is installed (here it comes with httpx, a development dependency, which `uv sync` installs by default; no runtime package needs it). That bundle is the "default trust store" this page means, not the operating system's. botocore's own bundled copy (`botocore/cacert.pem`, MPL-2.0) is used only when certifi can't be imported, so an install made with `uv sync` never reads it; the project lead approved it on certifi's terms (ADR-0037, 2026-11-21; [licences](licences.md)).

Every boto3 call runs in a worker thread that is never abandoned: a cancellation that arrives during a call takes effect when the call returns (bounded by the timeouts of up to three attempts and the back-off between them); the clean-up after it (closing a body, aborting an upload) is shielded. boto3 is imported only when `FOURCE_STORAGE=s3`. The `botocore`, `boto3` and `s3transfer` loggers stay at WARNING and `urllib3` at ERROR whatever the root level, because botocore logs request headers, Authorization included, at DEBUG, and urllib3's warnings name the store's host or a URL; never lower them. The client pools up to 40 connections, one for each of anyio's worker threads, so concurrent calls never overflow the pool.

What the adapter does with S3's answers:

- A not-found answer counts as a missing blob only for a read (`BlobMissing`, which the service reports as `file_damaged`) and for the bucket check. For a write, a delete or a probe it means the store can't be used: a proxy that answers 404 with no S3 error must not look like a missing blob.
- A TLS error part way through a body is `storage_unavailable`, because urllib3's own errors pass botocore's body reader unwrapped.
- `create_bucket` creates the bucket only when a `HEAD` says it is missing, and treats only `BucketAlreadyOwnedByYou` as already there (a bucket our own concurrent `migrate` just made). A bucket name another account holds is an error.
- Messages never carry botocore's error text, which names the endpoint; the S3 error code, or the error's class, is logged at most.

**The botocore facts this relies on** were read in botocore **1.44.5** (the locked version), in `.venv/lib/python3.12/site-packages/botocore/`. `core/storage/tests/test_s3_client.py` pins what they add up to; re-read these lines, and re-run that file, when boto3 is upgraded.

| File and lines | What it says | What 4CE does about it |
| --- | --- | --- |
| `configprovider.py` 57 and 353-441 | The table of session variables names the environment variables and the config-file keys each reads; `ConfigChainFactory` builds each chain from the session instance, then the environment, then the config file, then the default | Each chain is rebuilt from the instance variable and the default only, so neither the environment nor a file is in any of them |
| `session.py` 1255-1275 | The component named `config_store` is the supported place to replace a provider | `set_config_provider` there |
| `session.py` 391-426 and 438-462 | The config file and the credentials file, whose paths the `config_file` and `credentials_file` variables hold, are read to find profiles | Both paths are the null device |
| `session.py` 1038 | The scoped config of the profile goes into every client's setup | It comes from the empty files |
| `session.py` 198-201, `loaders.py` 237-263 | The default data loader searches `~/.aws/models` before botocore's own data | A loader that searches only `Loader.BUILTIN_DATA_PATH` is registered as the `data_loader` component |
| `session.py` 278-290 | Client-side monitoring starts when `csm_enabled` resolves true, and sends a datagram | The chain gives it its default, off |
| `plugin.py` 55-63, `session.py` 1172-1188 | Every new client imports the modules `BOTOCORE_EXPERIMENTAL__PLUGINS` names, unless the plugin context says `DISABLED` | The client is created inside a context set to `DISABLED` |
| `session.py` 961-967 | Explicit keys become the credentials, and no credential provider is asked | The keys come from 4CE's settings |
| `session.py` 1002-1009 and 1071-1087, `configprovider.py` 614-627 | A defaults mode other than `legacy` merges smart defaults, and `auto` may ask the instance metadata service for the region; the mode must be one botocore knows | `defaults_mode` is `legacy` |
| `session.py` 1089-1098, `args.py` 387-405 | A configured endpoint URL is looked up, unless an explicit one is given or `ignore_configured_endpoint_urls` is true | Both: an explicit endpoint, and the setting true |
| `endpoint.py` 412-413 and 435-438, `args.py` 170 and 301-302, `httpsession.py` 244-250 | Proxies come from the environment only when `proxies` is `None`; the client's value is passed through, and a proxy is looked up in that dict by URL scheme | `proxies={}` |
| `session.py` 948-949, `endpoint.py` 447-448 and 455-465 | A CA bundle is taken from `AWS_CA_BUNDLE` (through `ca_bundle`) or `REQUESTS_CA_BUNDLE` only when `verify` is `None`; an explicit value wins and is refused if blank | `verify=True` |
| `httpsession.py` 95-110 and 389-392 | With `verify` true, an `https` connection requires a certificate checked against `certifi.where()`, or botocore's own `cacert.pem` if certifi can't be imported | certifi is installed; see the trust store above |
| `args.py` 600-644 | The number of attempts and the retry mode come from the client's `retries` before the environment or a file | `retries={"mode": "standard", "total_max_attempts": N}` |
| `retries/standard.py` 373-405 | The wait before a retry is random between 0 and `min(base * 2^(attempt - 1), 20 s)`, the base being 50 ms (1 s when throttled), longer if the server sends `x-amz-retry-after` | Nothing: this is why the cancellation bound above includes the back-off |
| `auth.py` 338-361 and 501-540 | The signature covers the SHA-256 of the body unless S3 signing is turned off; an explicit `payload_signing_enabled` wins; otherwise an `https` request with a checksum header and a streaming body is not signed | `payload_signing_enabled` true (it changes nothing today, because 4CE asks for no checksum header; the test pins the outcome, the signed hash) |
| `httpchecksum.py` 327-382 | A request checksum is added only for an operation that requires one, or when the setting is `when_supported` | `request_checksum_calculation` and `response_checksum_validation` are `when_required` |
| `utils.py` 1749-1860 | A wrong-region answer is retried at once, with the new region in the signature and the endpoint re-resolved | The explicit endpoint stays, so the retry goes to the same host (pinned by the test) |

Some variables still reach botocore without changing where a request goes or who signs it. Run on 1.44.5 with a client from `make_s3_client`: `AWS_EXECUTION_ENV` adds `exec-env/<value>` to the user agent, `AWS_LAMBDA_FUNCTION_NAME` with `_X_AMZN_TRACE_ID` adds an `X-Amzn-Trace-Id` header, and `AWS_BEARER_TOKEN_S3` changes nothing in the request, which stays signed with `AWS4-HMAC-SHA256` (Signature Version 4). `SSLKEYLOGFILE` makes urllib3 write TLS keys, as the standard library does (`urllib3/util/ssl_.py` 321-322).

## Errors

| Code | Status | When |
| --- | --- | --- |
| `storage_unavailable` | 503 | The store can't be reached, refused the credentials, or has no bucket (`just migrate`), or the local store's folders can be changed by another account |
| `file_not_found` | 404 | No such file in this organisation, or it was deleted |
| `file_too_large` | 413 | Over `FOURCE_STORAGE_MAX_FILE_MB` |
| `file_damaged` | 500 | The bytes are missing or differ from the record |

Messages never carry an endpoint, key, path, file name or content; logs carry the S3 error code, or the error's class, at most.

## Known limits

- Bytes left by a caller that rolled back are not swept yet.
- Development uses MinIO's root credentials; per-purpose keys and bucket policies are a WP-F-10 follow-up.
- An abort that fails leaves an unfinished multipart upload in the store; 4CE doesn't sweep those either.
- An erasure that fails for good (30 attempts, about a day) leaves the bytes in place: the record keeps `deleted_at` set and `erased_at` empty, and its `storage.erase` job is `failed`. Until a sweep exists, those records are the ones to look for.
- On Windows the local store relies on the data folder's permissions (ACLs): keep it private, as for the ledger's signing key. On Linux and macOS the store refuses folders another account could change (Writing), so a store on a shared, group-writable or another account's folder doesn't start until its permissions are fixed (for example `chmod 700` on it). Accounts that come from a directory service may not be visible to that check ([the package README](../../core/storage/README.md#known-limits)).
- Files belong to one organisation: installation-wide files (pack bundles) need a later decision.
- The S3 client trusts only certifi's bundle: a MinIO with a private CA over HTTPS isn't supported yet (plain HTTP on the internal network is).

## Decisions

[ADR-0044](../adr/0044-file-storage-behind-one-interface.md) (proposed); [ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md) point 2 for botocore's CA bundle; ADR-0025 (MinIO and its patch source) is open.

## Acceptance

Everywhere, in `just test`: `core/storage/tests/` (the blob contract on the local folder, the S3 adapter through botocore's `Stubber`, the client's isolation from the environment against a stdlib fake server, the service and deleting on SQLite) and `apps/server/tests/` (health, the worker and `migrate`). On MinIO, in CI's MinIO job (`just test-minio`): the nine blob-contract tests, plus multipart uploads, creating the bucket twice, and a body changed after signing refused by the server (12 in all). On PostgreSQL, in CI's PostgreSQL job: `stored_files` under forced row-level security without `DELETE`, and the app role unable to reach or delete another organisation's files (`apps/server/tests/test_postgres.py`).
