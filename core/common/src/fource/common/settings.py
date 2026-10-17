from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """4CE's configuration, read from `FOURCE_*` environment variables or a local `.env`.

    Anything that holds a credential is a `SecretStr`, so it never shows up in logs or reprs.
    `Field(default=...)` marks a value as required, but set by the environment, not the caller.
    """

    model_config = SettingsConfigDict(env_prefix="FOURCE_", env_file=".env", extra="ignore")

    secret_key: SecretStr = Field(default=...)
    database_url: SecretStr = SecretStr("sqlite+aiosqlite:///data/fource.db")
    database_admin_url: SecretStr | None = None
    org: str = "default"
    token_ttl_minutes: int = Field(default=480, gt=0)
    redis_url: SecretStr | None = None
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: SecretStr | None = None
    s3_bucket: str = "fource"
    data_dir: Path = Path("data")
    offline: bool = True

    @field_validator("secret_key")
    @classmethod
    def _long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SECRET_LENGTH:
            raise ValueError(f"FOURCE_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters")
        return value
