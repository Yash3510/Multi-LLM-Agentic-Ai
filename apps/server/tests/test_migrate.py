import os
import sqlite3
from pathlib import Path

import pytest
from pydantic import SecretStr

from fource.common import Settings
from fource.server.migrate import alembic_config, downgrade, migration_url, upgrade


def tables(path: Path) -> set[str]:
    rows = sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {name for (name,) in rows}


def test_migrations_go_up_down_and_up_again(tmp_path: Path) -> None:
    path = tmp_path / "fource.db"
    url = f"sqlite+aiosqlite:///{path.as_posix()}"
    upgrade(url)
    assert {"orgs", "users", "revoked_tokens"} <= tables(path)
    slugs = sqlite3.connect(path).execute("SELECT slug FROM orgs").fetchall()
    assert slugs == [("default",)]
    downgrade(url, "base")
    assert "orgs" not in tables(path)
    assert not {"users", "revoked_tokens"} & tables(path)
    upgrade(url)
    assert "orgs" in tables(path)


def test_migrating_creates_the_folder_of_a_new_sqlite_file(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "fource.db"
    upgrade(f"sqlite+aiosqlite:///{path.as_posix()}")
    assert "orgs" in tables(path)


def test_a_percent_sign_in_the_url_reaches_alembic_intact() -> None:
    url = "postgresql+psycopg://fource:pa%25ss@localhost:5432/fource"
    assert alembic_config(url).get_main_option("sqlalchemy.url") == url


def test_migrations_use_the_admin_url_when_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # no .env from the repository
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)
    settings = Settings(
        secret_key=SecretStr("s" * 40),
        database_url=SecretStr("postgresql+psycopg://fource_app:a@localhost/fource"),
        database_admin_url=SecretStr("postgresql+psycopg://fource:o@localhost/fource"),
    )
    assert migration_url(settings) == "postgresql+psycopg://fource:o@localhost/fource"
    plain = Settings(
        secret_key=SecretStr("s" * 40), database_url=SecretStr("sqlite+aiosqlite:///x")
    )
    assert migration_url(plain) == "sqlite+aiosqlite:///x"
