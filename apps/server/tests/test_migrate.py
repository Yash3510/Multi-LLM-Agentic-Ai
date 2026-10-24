import os
import sqlite3
import uuid
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
    assert {"orgs", "users", "revoked_tokens", "ledger_entries", "ledger_heads"} <= tables(path)
    slugs = sqlite3.connect(path).execute("SELECT slug FROM orgs").fetchall()
    assert slugs == [("default",)]
    downgrade(url, "base")
    assert "orgs" not in tables(path)
    assert not {"users", "revoked_tokens", "ledger_entries", "ledger_heads"} & tables(path)
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


def test_the_ledger_refuses_updates_and_deletes_on_sqlite(tmp_path: Path) -> None:
    path = tmp_path / "fource.db"
    upgrade(f"sqlite+aiosqlite:///{path.as_posix()}")
    connection = sqlite3.connect(path)
    (org_id,) = connection.execute("SELECT id FROM orgs").fetchone()
    connection.execute(
        "INSERT INTO ledger_entries (id, org_id, created_at, seq, at, type, actor, refs, prev,"
        " hash) VALUES (?, ?, '2026-11-14 10:22:31', 1, '2026-11-14 10:22:31', 'checkpoint',"
        " 'system', '{}', ?, ?)",
        (uuid.uuid4().hex, org_id, "0" * 64, "1" * 64),
    )
    connection.commit()
    for statement in [
        "UPDATE ledger_entries SET actor = 'anonymous'",
        "DELETE FROM ledger_entries",
    ]:
        with pytest.raises(sqlite3.IntegrityError, match="insert-only"):
            connection.execute(statement)
    assert connection.execute("SELECT actor FROM ledger_entries").fetchall() == [("system",)]
    connection.close()
