import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from fource.common import Settings

SECRET = "x" * 40


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.chdir(Path(__file__).parent)  # so no stray .env file is picked up
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # nor anything already set in the developer's shell
    monkeypatch.setenv("FOURCE_SECRET_KEY", SECRET)
    return monkeypatch


def test_zero_setup_defaults(env: pytest.MonkeyPatch) -> None:
    settings = Settings()
    assert settings.database_url.get_secret_value() == "sqlite+aiosqlite:///data/fource.db"
    assert settings.database_admin_url is None
    assert (settings.org, settings.token_ttl_minutes, settings.offline) == ("default", 480, True)
    assert settings.redis_url is None and settings.s3_endpoint is None


def test_reads_prefixed_environment(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_DATABASE_URL", "postgresql+psycopg://fource_app:pw@localhost/fource")
    env.setenv("FOURCE_TOKEN_TTL_MINUTES", "30")
    settings = Settings()
    assert settings.database_url.get_secret_value().startswith("postgresql+psycopg://")
    assert settings.token_ttl_minutes == 30


def test_secrets_never_appear_in_output(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_DATABASE_URL", "postgresql+psycopg://fource_app:db-secret@localhost/x")
    shown = repr(Settings()) + str(Settings())
    assert SECRET not in shown and "db-secret" not in shown


def test_the_secret_key_is_required(env: pytest.MonkeyPatch) -> None:
    env.delenv("FOURCE_SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings()


def test_a_short_secret_key_is_refused(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_SECRET_KEY", "too-short")
    with pytest.raises(ValidationError, match="at least 32"):
        Settings()


def test_invalid_values_are_errors(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_TOKEN_TTL_MINUTES", "0")
    with pytest.raises(ValidationError):
        Settings()
