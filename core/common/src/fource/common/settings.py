import re
from ipaddress import AddressValueError, IPv6Address
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_LENGTH = 32
_BUCKET = re.compile(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]")
# A host label that is not all digits, as botocore requires of a region (validate_region_name).
_REGION = re.compile(r"(?![0-9]+$)[a-z0-9](?:[a-z0-9-]{0,30}[a-z0-9])?")
_HOST = re.compile(r"((?!-)[a-z0-9-]{1,63}(?<!-)\.)*(?!-)[a-z0-9-]{1,63}(?<!-)\.?")


def _plain_http_url(value: str, *, path_allowed: bool) -> bool:
    """http:// or https:// with a host and an optional port (and path, if allowed); never a
    user, password, query or fragment, which would hide credentials or change the request.
    Only printable ASCII: urlsplit strips control characters and folds look-alike letters, so
    the value it parses would not be the value that was set."""
    if not (value.isascii() and value.isprintable()) or "?" in value or "#" in value:
        return False
    try:
        parts = urlsplit(value)
        port = parts.port  # raises ValueError when it isn't a number from 0 to 65535
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not parts.hostname or port == 0:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if parts.query or parts.fragment:
        return False
    return path_allowed or parts.path in ("", "/")


def _s3_host(url: str) -> bool:
    """Whether botocore takes the URL's host: letters, digits and hyphens between dots, or an
    IPv6 address (utils.is_valid_endpoint_url). It refuses any other host only when the client
    is made, with a message that holds the URL. A bracketed host must be a plain IPv6 address:
    botocore also refuses a zone id (`%`) with unusual characters and the IPvFuture form."""
    host = urlsplit(url).hostname or ""
    if ":" in host:
        try:
            IPv6Address(host)
        except AddressValueError:
            return False
        return "%" not in host
    return len(host) <= 255 and _HOST.fullmatch(host) is not None


class Settings(BaseSettings):
    """4CE's configuration, read from `FOURCE_*` environment variables or a local `.env`.

    Anything that holds a credential is a `SecretStr`, so it never shows up in logs or reprs.
    `Field(default=...)` marks a value as required, but set by the environment, not the caller.
    """

    model_config = SettingsConfigDict(
        env_prefix="FOURCE_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    secret_key: SecretStr = Field(default=...)
    database_url: SecretStr = SecretStr("sqlite+aiosqlite:///data/fource.db")
    database_admin_url: SecretStr | None = None
    org: str = "default"
    token_ttl_minutes: int = Field(default=480, gt=0)
    redis_url: SecretStr | None = None
    storage: Literal["local", "s3"] = "local"
    storage_max_file_mb: int = Field(default=512, gt=0, le=65_536)
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: SecretStr | None = None
    s3_bucket: str = "fource"
    s3_region: str = "us-east-1"
    data_dir: Path = Path("data")
    ledger_key_file: Path | None = None
    ledger_checkpoint_minutes: int | None = Field(default=None, gt=0, le=525_600)  # a year
    signin_attempts_per_minute: int = Field(default=30, gt=0)
    offline: bool = True

    @field_validator("secret_key")
    @classmethod
    def _long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SECRET_LENGTH:
            raise ValueError(f"FOURCE_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters")
        return value

    @field_validator("s3_endpoint")
    @classmethod
    def _plain_endpoint(cls, value: str | None) -> str | None:
        if value is not None and not (
            _plain_http_url(value, path_allowed=False) and _s3_host(value)
        ):
            raise ValueError(
                "FOURCE_S3_ENDPOINT is http:// or https://, a host and an optional port, "
                "with no path, user, query or fragment; the host is letters, digits and "
                "hyphens between dots, or an IPv6 address"
            )
        return value

    @field_validator("s3_bucket")
    @classmethod
    def _bucket_name(cls, value: str) -> str:
        if not _BUCKET.fullmatch(value):
            raise ValueError(
                "FOURCE_S3_BUCKET is 3 to 63 lower-case letters, digits and hyphens, "
                "starting and ending with a letter or digit"
            )
        return value

    @field_validator("s3_region")
    @classmethod
    def _region_name(cls, value: str) -> str:
        if not _REGION.fullmatch(value):
            raise ValueError(
                "FOURCE_S3_REGION is 1 to 32 lower-case letters, digits and hyphens, starting "
                "and ending with a letter or digit, and not all digits"
            )
        return value

    @model_validator(mode="after")
    def _s3_is_complete(self) -> Self:
        if self.storage == "s3":
            secret = self.s3_secret_key.get_secret_value() if self.s3_secret_key else None
            given = {
                "FOURCE_S3_ENDPOINT": self.s3_endpoint,
                "FOURCE_S3_ACCESS_KEY": self.s3_access_key,
                "FOURCE_S3_SECRET_KEY": secret,
            }
            # A blank value, as a container environment can leave one, is a missing key.
            missing = [name for name, value in given.items() if not value or not value.strip()]
            if missing:
                raise ValueError(f"FOURCE_STORAGE=s3 needs {', '.join(missing)}")
        return self
