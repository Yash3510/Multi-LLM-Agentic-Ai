import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from fource.common import Settings

SECRET = "x" * 40


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> pytest.MonkeyPatch:
    monkeypatch.chdir(tmp_path)  # an empty folder, so no stray .env file is picked up
    for name in [n for n in os.environ if n.upper().startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # nor anything set in the developer's shell, in any letter case
    monkeypatch.setenv("FOURCE_SECRET_KEY", SECRET)
    return monkeypatch


@pytest.fixture
def lower_case_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("fource_storage", "s3")  # set before `env` runs, as a shell export would be


def test_the_environment_fixture_clears_lower_case_names_too(
    lower_case_storage: None, env: pytest.MonkeyPatch
) -> None:
    assert Settings().storage == "local"  # settings read names case-insensitively


def test_zero_setup_defaults(env: pytest.MonkeyPatch) -> None:
    settings = Settings()
    assert settings.database_url.get_secret_value() == "sqlite+aiosqlite:///data/fource.db"
    assert settings.database_admin_url is None
    assert (settings.org, settings.token_ttl_minutes, settings.offline) == ("default", 480, True)
    assert settings.redis_url is None and settings.s3_endpoint is None
    assert settings.ledger_key_file is None
    assert settings.ledger_checkpoint_minutes is None  # scheduled checkpoints are off


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


def test_a_refused_secret_key_is_not_echoed_in_the_error(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_SECRET_KEY", "short-value-abc")
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "short-value-abc" not in str(refused.value)


def test_invalid_values_are_errors(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_TOKEN_TTL_MINUTES", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_scheduled_checkpoints_are_switched_on_by_a_positive_interval(
    env: pytest.MonkeyPatch,
) -> None:
    env.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "1440")
    assert Settings().ledger_checkpoint_minutes == 1440
    env.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_the_checkpoint_interval_is_at_most_a_year(env: pytest.MonkeyPatch) -> None:
    # An interval beyond datetime's range would fail when the worker adds it to a date, long
    # after start-up: Settings refuses it at once, naming the variable.
    env.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "525600")
    assert Settings().ledger_checkpoint_minutes == 525600
    env.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "525601")
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "ledger_checkpoint_minutes" in str(refused.value)


def test_the_sign_in_limit_is_a_positive_number_of_attempts_a_minute(
    env: pytest.MonkeyPatch,
) -> None:
    assert Settings().signin_attempts_per_minute == 30
    env.setenv("FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE", "100")
    assert Settings().signin_attempts_per_minute == 100
    env.setenv("FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE", "0")
    with pytest.raises(ValidationError):
        Settings()


def test_storage_defaults(env: pytest.MonkeyPatch) -> None:
    settings = Settings()
    assert (settings.storage, settings.storage_max_file_mb) == ("local", 512)
    assert (settings.s3_bucket, settings.s3_region) == ("fource", "us-east-1")


def test_s3_storage_needs_its_endpoint_and_both_keys(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_STORAGE", "s3")
    with pytest.raises(ValidationError) as refused:
        Settings()
    message = str(refused.value)
    for name in ("FOURCE_S3_ENDPOINT", "FOURCE_S3_ACCESS_KEY", "FOURCE_S3_SECRET_KEY"):
        assert name in message
    env.setenv("FOURCE_S3_ENDPOINT", "http://localhost:9000")
    env.setenv("FOURCE_S3_ACCESS_KEY", "fource")
    env.setenv("FOURCE_S3_SECRET_KEY", "s3-secret-value")
    settings = Settings()
    assert settings.storage == "s3"
    assert "s3-secret-value" not in repr(settings) + str(settings)


@pytest.mark.parametrize(
    ("name", "blank"),
    [("FOURCE_S3_SECRET_KEY", "   "), ("FOURCE_S3_ACCESS_KEY", "\t")],
)
def test_a_blank_s3_key_is_a_missing_key(env: pytest.MonkeyPatch, name: str, blank: str) -> None:
    env.setenv("FOURCE_STORAGE", "s3")
    env.setenv("FOURCE_S3_ENDPOINT", "http://localhost:9000")
    env.setenv("FOURCE_S3_ACCESS_KEY", "fource")
    env.setenv("FOURCE_S3_SECRET_KEY", "s3-secret-value")
    env.setenv(name, blank)
    with pytest.raises(ValidationError) as refused:
        Settings()
    message = str(refused.value)
    assert name in message
    assert repr(blank) not in message and f"={blank}" not in message
    assert "s3-secret-value" not in message


@pytest.mark.parametrize(
    "endpoint",
    [
        "localhost:9000",
        "ftp://localhost:9000",
        "http://user:pw-secret-123@localhost:9000",
        "http://localhost:9000/bucket",
        "http://localhost:9000?x=1",
        "http://localhost:99999",
        "http:// localhost:9000",
        " http://localhost:9000",  # urlsplit strips a leading space too
        "http://localhost:9000 ",
        "http://localhost:9000/ ",
        "http://fource_minio_1:9000",  # botocore refuses these hosts when the client is made
        "http://-minio:9000",
        "http://[fe80::1%eth0:1]:9000",  # botocore refuses a zone id and an IPvFuture host
        "http://[fe80::1%en$]:9000",
        "http://[v1.a:b]:9000",
        "http://[vF.x:y]:9000",
        "http://localhost:9000?",  # urlsplit drops an empty query or fragment
        "http://localhost:9000#",
        "\x01http://localhost:9000",  # and strips a leading control character
        "\x1bhttp://localhost:9000",
        "http://\u212ainio:9000",  # the Kelvin sign folds to a plain k
    ],
)
def test_an_endpoint_is_scheme_host_and_port_only(env: pytest.MonkeyPatch, endpoint: str) -> None:
    env.setenv("FOURCE_S3_ENDPOINT", endpoint)
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "FOURCE_S3_ENDPOINT" in str(refused.value)
    assert "pw-secret-123" not in str(refused.value)


def test_a_plain_endpoint_is_kept(env: pytest.MonkeyPatch) -> None:
    for endpoint in (
        "http://localhost:9000",
        "https://minio.internal",
        "http://[::1]:9000/",
        "http://[::]:9000",
        "http://[2001:db8::1]:9000",
        "http://[::ffff:127.0.0.1]:9000",
        "http://[::1.2.3.4]:9000",
        "http://[1:2:3:4:5:6:7::]:9000",
    ):
        env.setenv("FOURCE_S3_ENDPOINT", endpoint)
        assert Settings().s3_endpoint == endpoint


@pytest.mark.parametrize("bucket", ["Fource", "ab", "fource_files", "-fource", "fource-", "a" * 64])
def test_a_bucket_name_follows_the_s3_rules(env: pytest.MonkeyPatch, bucket: str) -> None:
    env.setenv("FOURCE_S3_BUCKET", bucket)
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "FOURCE_S3_BUCKET" in str(refused.value)


def test_a_refused_bucket_name_is_not_echoed(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_S3_BUCKET", "Bad_Bucket_Marker")
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "FOURCE_S3_BUCKET" in str(refused.value)
    assert "Bad_Bucket_Marker" not in str(refused.value)


@pytest.mark.parametrize("region", ["EU Central", "us-", "123"])
def test_a_region_is_one_lower_case_word(env: pytest.MonkeyPatch, region: str) -> None:
    env.setenv("FOURCE_S3_REGION", "eu-central-1")
    assert Settings().s3_region == "eu-central-1"
    env.setenv("FOURCE_S3_REGION", region)  # botocore refuses "us-" and "123" too, but later
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "FOURCE_S3_REGION" in str(refused.value)


def test_a_refused_region_is_not_echoed(env: pytest.MonkeyPatch) -> None:
    env.setenv("FOURCE_S3_REGION", "Bad_Region_Marker")
    with pytest.raises(ValidationError) as refused:
        Settings()
    assert "FOURCE_S3_REGION" in str(refused.value)
    assert "Bad_Region_Marker" not in str(refused.value)


@pytest.mark.parametrize(
    ("name", "good", "bad"),
    [
        ("FOURCE_STORAGE_MAX_FILE_MB", "65536", "65537"),
        ("FOURCE_STORAGE_MAX_FILE_MB", "1", "0"),
        ("FOURCE_STORAGE", "local", "minio"),
    ],
)
def test_limits_and_choices(env: pytest.MonkeyPatch, name: str, good: str, bad: str) -> None:
    env.setenv(name, good)
    Settings()
    env.setenv(name, bad)
    with pytest.raises(ValidationError):
        Settings()
