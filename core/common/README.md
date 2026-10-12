# fource-common

Shared building blocks that every 4CE core package may depend on. It depends on no other 4CE package.

**Owner:** R1

## Public API

| Name | What it is |
| --- | --- |
| `Settings` | 4CE's typed configuration, read from `FOURCE_*` environment variables or a local `.env` file. Credentials are `SecretStr`, so they never appear in logs. Missing or invalid values fail at start-up. |

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
