from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """4CE's configuration, read from `FOURCE_*` environment variables or a local `.env`.

    Anything that holds a credential is a `SecretStr`, so it never shows up in logs or reprs.
    `Field(default=...)` marks a value as required, but set by the environment, not the caller.
    """

    model_config = SettingsConfigDict(env_prefix="FOURCE_", env_file=".env", extra="ignore")

    database_url: SecretStr = Field(default=...)
    redis_url: SecretStr = Field(default=...)
    s3_endpoint: str = Field(default=...)
    s3_access_key: str = Field(default=...)
    s3_secret_key: SecretStr = Field(default=...)
    s3_bucket: str = "fource"
    data_dir: Path = Path("data")
    offline: bool = True
