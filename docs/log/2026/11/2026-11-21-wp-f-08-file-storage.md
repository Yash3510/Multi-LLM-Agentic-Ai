---
title: "File storage"
type: log
status: implemented
owner: R1
updated: 2026-11-21
date: 2026-11-21
branch: 4ce-core
pr: null
work_package: "WP-F-08"
author: Yash3510
areas: [core/storage, core/common, core/ledger, apps/server, tools, .github/workflows, docs]
tags: [4ce, log, storage, security]
---

# File storage

## What changed

- **`core/storage`** (new): files per organisation behind one protocol, `Blobs`, with two adapters ([file storage](../../../architecture/storage.md)).
  - `LocalBlobs` keeps bytes under `<FOURCE_DATA_DIR>/files` as `<organisation hex>/<file hex>`. A write goes to an exclusive part file, is synced and is renamed into place. Links and junctions are refused. On Linux and macOS the store is used only when no other account can change its folders or one above them.
  - `S3Blobs` keeps bytes in a bucket (MinIO). One `put_object` up to 8 MiB, else a multipart upload that holds about two parts in memory and aborts on failure or cancellation. S3's not-found answers count as a missing blob only for reads and the bucket check; a TLS error part way through a body is `storage_unavailable`; `create_bucket` treats only `BucketAlreadyOwnedByYou` as already there; a cancellation during the final call takes effect after it.
  - `make_s3_client` builds the only boto3 client: a botocore session that reads no `AWS_*` variable and no `~/.aws` file, an explicit endpoint, keys and region, TLS checked against certifi's bundle, no proxy, path-style addressing, 5 s to connect, 60 s to read and three attempts, and a second client for health that tries once for 2 s. The page lists the botocore 1.44.5 files and lines this rests on.
  - `Storage` adds the records and the ledger: `put` meters the size and SHA-256, writes the bytes, then the `stored_files` row and a `file.write` entry; `stat` and `open` find the row in the caller's organisation first; a `Reading` is read once, stops a blob longer than its record at the recorded size and checks size and SHA-256 at the end (the caller already holds the chunks before any `file_damaged`); a caller that rolls back after `put` leaves an unreferenced blob (ADR-0044, point 6).
  - `Storage.delete` marks the record, writes `file.delete` and queues `storage.erase` (30 attempts, key `storage.erase:<file id>`) in one transaction; of two deletes at once the second gets `file_not_found`. `erase` deletes the bytes of a deleted, not yet erased file and sets `erased_at`; it leaves another organisation's file alone, and the worker's handler holds a 5 minute lease.
  - Four errors: `storage_unavailable` (503), `file_not_found` (404), `file_too_large` (413), `file_damaged` (500).
- **Migrations `0006` and `0007`:** `stored_files` under forced row-level security with `SELECT`, `INSERT` and `UPDATE` for the app role, no `DELETE`, and the check `stored_files_size`; then the SQLite trigger `stored_files_no_delete`, so a stray `DELETE` fails on the development engine too.
- **Settings:** `FOURCE_STORAGE` (`local` | `s3`), `FOURCE_STORAGE_MAX_FILE_MB` (512, 1 to 65536), `FOURCE_S3_REGION` (`us-east-1`), with checks on the endpoint, bucket, region and blank keys, beside the existing `FOURCE_S3_*`.
- **Ledger:** the entry types `file.write` (plain SHA-256 of the content as the output hash; refs `file`, `size`, `content_type`) and `file.delete` (ref `file`).
- **Server:** health reports `storage` (`ok` or `unavailable`, 503 when unavailable); `fource-server migrate` creates the bucket with `FOURCE_STORAGE=s3` (`Created the bucket …` or `Found the bucket …`); `fource-server worker` always runs `storage.erase` and opens the store before it checks its database role; a database from before `0006` is refused with the "run `just migrate`" message.
- **Commit-message check** (`tools/commit_words.py`, the commit-msg hook): refuses sector terms, tool names, attribution and words about how the work was organised, with the fix for the `#` lines git keeps ([repository](../../../architecture/repository.md)).
- **CI:** a `minio` job builds the image compose uses and runs `just test-minio`. It is the one CI change of this work package, approved by the project lead on 2026-11-02 (AGENTS.md §3 reserves CI changes for humans).
- **Commits:** from `9c332e4` (the end of slice 3) to `10e51b3` (the trunk before this entry), 114 non-merge commits touch the storage, ledger, settings, database, jobs, server, tools and workflow paths, ADR-0044 and ADR-0037, `pyproject.toml`, `uv.lock` and `.env.example`; 73 of them touch `core/storage`, 14 `apps/server`, 8 `core/common`. The count includes the commit-message check and slice 3's follow-ups.

## Why

WP-F-08. Originals, renders, deliverables and index snapshots need a home that keeps one organisation's files away from another's, hashes every write into the ledger, and lets a file be deleted without touching a ledger that only holds hashes. Ingest (WP-KN-01), the sandbox and the deliverables build on it.

## Files

| Path | Change |
| --- | --- |
| `core/storage/src/fource/storage/` (`base`, `errors`, `keys`, `local`, `models`, `s3`, `service`, `__init__`) | new: the protocol, the two adapters, the records, `Storage`, `open_storage` |
| `core/storage/tests/` | new: keys, records, the blob contract (local and MinIO), the local adapter, the S3 adapter through botocore's `Stubber`, the client's isolation against a stdlib fake server, the service, deleting, MinIO-only tests |
| `core/storage/README.md`, `pyproject.toml` | new |
| `core/common/src/fource/common/settings.py` and its tests | the storage settings and their checks |
| `core/ledger/src/fource/ledger/chain.py` | `EntryType.FILE_WRITE`, `EntryType.FILE_DELETE` |
| `apps/server/src/fource/server/migrations/versions/0006_create_stored_files.py`, `0007_stored_files_never_deleted.py`, `env.py` | the records and the SQLite delete guard |
| `apps/server/src/fource/server/` (`main.py`, `deps.py`, `routes/health.py`, `cli.py`, `worker.py`) | the file store in the app, health, `migrate` and the worker |
| `apps/server/tests/` | health, `create_app`, the worker, `migrate`, the migrated schema and PostgreSQL |
| `tools/commit_words.py`, `tools/tests/test_commit_words.py`, `.pre-commit-config.yaml` | the commit-message check |
| `tools/licence-review.toml` | s3transfer, python-dateutil, and botocore with its approval |
| `.github/workflows/ci.yml` | the `minio` job |
| `pyproject.toml`, `justfile`, `uv.lock`, `.env.example` | the S3 and layers contracts, the `minio` marker, `just test-minio`, `just test`, the locked packages, `FOURCE_STORAGE` |
| `docs/architecture/storage.md` | new page |
| `docs/architecture/` (`api`, `database`, `ledger`, `jobs`, `services`, `licences`, `repository`, `overview`, `README`), `docs/README.md`, `docs/state.md`, `docs/log/README.md`, this entry | what storage added |

## How it was verified

On `vps` (Debian, Python 3.12.15, 2 cores), 2026-11-21, at `b4f3487` (the docs commit; storage's code is unchanged since `10e51b3`). Each check ran alone.

1. **Ruff, pyright, contracts:** `uv run ruff check --no-cache .`: `All checks passed!`; `uv run ruff format --no-cache --check .`: `225 files already formatted`; `uv run pyright`: `0 errors, 0 warnings, 0 informations`; `just imports`: `Contracts: 14 kept, 0 broken.` (including "Only the public API of fource.storage is imported from outside it" and "S3 is reached only through fource.storage").
2. **Instead of `just check`** (its web steps belong to the web app, and are not run here), the recipes as separate commands: `just lint imports repo-check neutrality && just docs && just licences secrets test`: exit 0. Repo and neutrality checks clean; `just docs` clean (no `--base`, so the work-log, drift and ADR rules were skipped); `78 components checked`, `114 files scanned`, `5 bundled services checked`; gitleaks over the branch history passed; `807 passed, 97 deselected in 123.62s`. The 97 are the 44 PostgreSQL, 41 Redis and 12 MinIO tests. Collected without them: `core/storage` 97, `core/ledger` 126, `core/jobs` 64, `core/live` 64, `core/db` 30, `core/identity` 59, `core/common` 59, `core/packs` 16, `apps/server` 171, `tools` 121.
3. **PostgreSQL on a throwaway container** (`postgres:18.6-alpine` by digest, `127.0.0.1:55432`, throwaway passwords in the environment; the shared `services-postgres-1` was never touched): `FOURCE_TEST_POSTGRES_PORT=55432 … uv run pytest -m postgres -q`: `44 passed, 860 deselected in 116.50s`, with the two `stored_files` tests (forced row-level security without `DELETE`; the app role cannot reach or delete another organisation's files). Both were seen failing before migration `0006` existed (`relation "stored_files" does not exist`, 2 failed) when they were written. The container was removed.
4. **MinIO on a throwaway container** (the existing image `fource/minio:RELEASE.2025-10-15T17-29-55Z`, never rebuilt, `127.0.0.1:59000`): `just test-minio` with the three `FOURCE_TEST_S3_*` variables: `12 passed, 892 deselected in 11.14s` (the nine blob-contract tests in `test_blobs.py`, three in `test_minio.py`, among them the server refusing a body changed after signing). The MinIO tests could not be seen failing for a behaviour first on vps's SQLite run: without a server they fail by design (`3 failed, 9 errors`, never skipped), and with one they passed the first time.
5. **`migrate` creates the bucket** (same container; an empty folder so no `.env` applied; `FOURCE_STORAGE=s3`, bucket `fource-done-when`), run twice:
   - first run: `The database is up to date.`, `Created the bucket fource-done-when.`, exit 0;
   - second run: `The database is up to date.`, `Found the bucket fource-done-when.`, exit 0.
   Both containers were removed; `docker ps` showed only `services-postgres-1` and `services-redis-1`.
6. **A fresh clone on SQLite and local files** (`git clone` of this checkout at `b4f3487` into a scratch folder; only the Python parts of `just setup` ran, `uv sync --all-packages --locked` and `uv run python tools/dev/env.py`, which wrote a `.env` with `FOURCE_STORAGE=local`; `npm ci` and the git hooks were skipped), then:
   - `just migrate`: `The database is up to date.`
   - a script that opens the store from `Settings()`, writes `hello.txt`, reads it back and deletes it: printed `hello from slice 4`; `find data/files -type f | wc -l`: `1`.
   - `just worker --once`: `Ran 1 job attempt.`, exit 0, no line saying `failed`; `find data/files -type f | wc -l`: `0` (the erasure ran).
   - `just ledger keygen`, `just ledger checkpoint` (signed entry 2), `just ledger verify`: `Ledger of default: 3 entries, head 3.`, `A signed checkpoint vouches for it up to entry 2.`, `Verified.`, exit 0 (`file.write`, `file.delete` and the checkpoint).
7. **botocore facts:** each file and line on the page was read in botocore 1.44.5. Run on that version with a client from `make_s3_client`: `AWS_EXECUTION_ENV` appears in the user agent as `exec-env/<value>`, `AWS_LAMBDA_FUNCTION_NAME` with `_X_AMZN_TRACE_ID` adds the `X-Amzn-Trace-Id` header, and `AWS_BEARER_TOKEN_S3` leaves the request signed with `AWS4-HMAC-SHA256`.
8. **CI on GitHub:**
   - The first run with the MinIO job: `44930492356` (pushed at `10e51b3`).
   - Its results:
     - `just check` on ubuntu-latest and on macos-latest: green, 807 passed and 97 deselected.
     - PostgreSQL tests: 44 passed. Redis tests: 41 passed.
     - MinIO tests: 12 passed and 892 deselected. The runner built the image from its tag, MinIO answered on 127.0.0.1:9000, and the readiness loop held.
     - `just check` on windows-latest: its Python tests passed (807 passed, 97 deselected). It then failed only in the web app's browser test `e2e/sign-in.spec.ts`, where a signed-out visit to `/` doesn't reach the sign-in page on Windows. That test has failed the same way since the web app's sign-in work of 2026-11-17 (`31b8e9c`), before any storage commit of that day. It is the web app's to fix and lies outside file storage.
9. **Not run:** the full `just check` (its web steps); the `docker build` of the MinIO image on vps (the image was already there; CI built it from its tag, item 8); PostgreSQL from a Windows host (not exercised anywhere); a MinIO over HTTPS with a private CA (not supported).

## Decisions

- [ADR-0044](../../../adr/0044-file-storage-behind-one-interface.md), proposed: the package, the two adapters, boto3 configured so that nothing outside 4CE's settings steers it, keys made of ids, records under row-level security, writing, reading and deleting.
- **The project lead's answers of 2026-11-02:** boto3 as the S3 client (4CE's own signing is a rejected alternative); the MinIO job in CI, the one CI change of this work package; MinIO's image built once on vps; no `file.erase` ledger entry, the record's `erased_at` being its evidence.
- **2026-11-11:** the folder rule (option A): on Linux and macOS the local store refuses a store or organisation folder another account owns or may write to (group write only for the owner's private group), and a folder above it that others may write to unless it is sticky; Windows relies on the data folder's ACLs.
- **2026-11-14:** a SQLite trigger refusing `DELETE` on `stored_files` (migration `0007`), as PostgreSQL's grants refuse it.
- **2026-11-21:** botocore's bundled CA list (`botocore/cacert.pem`, MPL-2.0) is approved on certifi's terms ([ADR-0037](../../../adr/0037-licence-approvals-for-the-backend-stack.md), point 2): used unmodified, and never read, because botocore uses certifi's copy when certifi is installed.

## New dependency

Runtime (installed everywhere, used only for `FOURCE_STORAGE=s3`): boto3 1.44.5, botocore 1.44.5 and s3transfer 0.19.3 (Apache-2.0), jmespath 1.1.0, six 1.17.0 and urllib3 2.8.0 (MIT), python-dateutil 2.9.0.post0 (Apache-2.0 and BSD-3-Clause). Development stubs (MIT): types-boto3-lite 1.44.3, types-boto3-s3 1.44.0, botocore-stubs 1.43.126, types-s3transfer 0.19.3. `tools/licence-review.toml` gained three package entries and one approval:

- **s3transfer 0.19.3:** its LICENSE.txt is the Apache 2.0 text and NOTICE.txt a one-line copyright notice; the metadata names a classifier the gate can't match.
- **python-dateutil 2.9.0.post0:** its LICENSE puts contributions since 2017-12-01 under Apache-2.0 and all the code under BSD-3-Clause; the metadata says only "Dual License".
- **botocore 1.44.5:** `Apache-2.0 AND MPL-2.0`, read from LICENSE.txt and NOTICE (the code is Apache-2.0; the NOTICE puts the CA root certificates under MPL-2.0), with an `[[approved]]` entry naming ADR-0037.

## Docs updated

`docs/architecture/storage.md` (new), `api.md` (the storage settings, health's `storage`, the four errors, `migrate` and the bucket, the worker and `storage.erase`), `database.md` (`0006`, `0007`, the worker's refusal before `0006`), `ledger.md` (`file.write`, `file.delete`), `jobs.md` (`storage.erase`), `services.md` (MinIO), `licences.md` (the S3 packages, the entries and botocore's CA bundle), `repository.md` (the layers, the S3 contract, `just test-minio`, `just test`), `overview.md`, `architecture/README.md`, `docs/README.md`, `core/storage/README.md` and `docs/state.md`.

## Known limits and follow-ups

- Bytes left by a caller that rolled back are not swept, and neither are unfinished multipart uploads.
- An erasure that fails for good (30 attempts, about a day) leaves the bytes in place with `erased_at` empty.
- Development uses MinIO's root credentials; per-purpose keys and bucket policies are a WP-F-10 follow-up.
- No private CA for an HTTPS MinIO: the client trusts only certifi's bundle.
- Files belong to one organisation; installation-wide files (pack bundles) need a later decision.
- On Windows the local store relies on the data folder's ACLs. On Linux and macOS the private-folder check cannot see accounts that come from a directory service.
- The botocore facts on the storage page are to be re-read, and `core/storage/tests/test_s3_client.py` re-run, when boto3 is upgraded.
- ADR-0044 stays proposed until R1 and R4 accept it; ADR-0025 (MinIO's patch source) is open.
- The model gateway (WP-MD-01) is not part of this entry.
