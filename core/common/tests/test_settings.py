import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from fource.common import Settings

REQUIRED = {
    "FOURCE_DATABASE_URL": "postgresql://fource:db-secret@localhost:5432/fource",
    "FOURCE_REDIS_URL": "redis://:redis-secret@localhost:6379/0",
    "FOURCE_S3_ENDPOINT": "http://localhost:9000",
    "FOURCE_S3_ACCESS_KEY": "fource",
    "FOURCE_S3_SECRET_KEY": "s3-secret",
}


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.chdir(Path(__file__).parent)  # so no stray .env file is picked up
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # nor anything already set in the developer's shell
    for name, value in REQUIRED.items():
        monkeypatch.setenv(name, value)
    return monkeypatch


def test_reads_prefixed_environment(env: pytest.MonkeyPatch) -> None:
    settings = Settings()
    assert settings.s3_endpoint == "http://localhost:9000"
    assert settings.database_url.get_secret_value() == REQUIRED["FOURCE_DATABASE_URL"]


def test_offline_by_default(env: pytest.MonkeyPatch) -> None:
    assert Settings().offline is True


def test_secrets_never_appear_in_output(env: pytest.MonkeyPatch) -> None:
    shown = repr(Settings()) + str(Settings())
    for secret in ("db-secret", "redis-secret", "s3-secret"):
        assert secret not in shown


def test_missing_setting_is_an_error(env: pytest.MonkeyPatch) -> None:
    env.delenv("FOURCE_DATABASE_URL")
    with pytest.raises(ValidationError):
        Settings()


def test_invalid_value_is_an_error(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_OFFLINE", "sometimes")
    with pytest.raises(ValidationError):
        Settings()
