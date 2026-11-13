# fource-common

Shared building blocks that every 4CE core package may depend on. It depends on no other 4CE package.

**Owner:** R1

## Public API

| Name | What it is |
| --- | --- |
| `Settings` | 4CE's typed configuration, read from `FOURCE_*` environment variables or a local `.env` file. Credentials are `SecretStr`, so they never appear in logs. Missing or invalid values fail at start-up. `FOURCE_SECRET_KEY` (at least 32 characters) is required; everything else has a default, so the server starts on SQLite with no other setup. `FOURCE_LEDGER_KEY_FILE` is the ledger's signing key (default `<FOURCE_DATA_DIR>/ledger/signing-key.pem`). `FOURCE_LEDGER_CHECKPOINT_MINUTES` turns on scheduled checkpoints, every so many minutes, from 1 to 525600 (a year; unset: off). `FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE` (30) caps sign-ins per client address per minute. `FOURCE_STORAGE` is `local` (files under `<FOURCE_DATA_DIR>/files`, the default) or `s3` (needs `FOURCE_S3_ENDPOINT`, `FOURCE_S3_ACCESS_KEY` and `FOURCE_S3_SECRET_KEY`; `FOURCE_S3_BUCKET` `fource`, `FOURCE_S3_REGION` `us-east-1`); `FOURCE_STORAGE_MAX_FILE_MB` (512) caps one file. The endpoint is checked at start-up and never echoed. |
| `new_id()` | A new UUIDv7. Ids made in one process sort in creation order; ids from different processes sort by millisecond. |
| `now()`, `set_clock()` | The current time, aware and in UTC; tests replace the clock with `set_clock(fn)` and restore it with `set_clock(None)`. |
| `FourceError` | The base of every error a person or client can act on: a stable `code`, an HTTP `status` and a `message`. |

```python
from fource.common import Settings

settings = Settings()
settings.offline  # True unless FOURCE_OFFLINE says otherwise
```

Every setting, with a safe placeholder, is listed in [`.env.example`](../../.env.example).

## Tests

```
uv run pytest core/common
```
