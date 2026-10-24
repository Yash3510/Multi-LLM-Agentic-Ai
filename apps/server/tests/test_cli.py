import asyncio
import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from fource.server import cli, loops

PASSWORD = "correct horse battery"


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)  # no .env from the repository
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # a shell's admin URL must never reach a real database
    monkeypatch.setenv("FOURCE_SECRET_KEY", "s" * 40)
    database = tmp_path / "cli.db"
    monkeypatch.setenv("FOURCE_DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    return database


def test_migrate_creates_the_tables(env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["migrate"]) == 0
    assert "up to date" in capsys.readouterr().out
    names = {n for (n,) in sqlite3.connect(env).execute("SELECT name FROM sqlite_master")}
    assert {"orgs", "users"} <= names


def test_create_user_asks_for_the_password_twice(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["migrate"])
    answers = iter([PASSWORD, PASSWORD])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    code = cli.main(["create-user", "Ada@Example.com", "--role", "Admin", "--name", "Ada"])
    assert code == 0 and "ada@example.com" in capsys.readouterr().out
    row = sqlite3.connect(env).execute("SELECT email, display_name, roles FROM users").fetchone()
    assert row == ("ada@example.com", "Ada", '["Admin"]')


def test_mismatched_passwords_create_nothing(env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli.main(["migrate"])
    answers = iter([PASSWORD, "something else entirely"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    assert cli.main(["create-user", "ada@example.com", "--role", "Admin"]) == 1
    assert sqlite3.connect(env).execute("SELECT count(*) FROM users").fetchone() == (0,)


def test_errors_are_reported_not_raised(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["migrate"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "short")
    assert cli.main(["create-user", "ada@example.com", "--role", "Admin"]) == 1
    assert "12" in capsys.readouterr().out


def test_create_user_before_migrating_says_so(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("getpass.getpass", lambda prompt="": PASSWORD)
    assert cli.main(["create-user", "ada@example.com", "--role", "Admin"]) == 1
    assert "migrate" in capsys.readouterr().out


def test_windows_gets_the_selector_loop_everywhere() -> None:
    assert loops.uvicorn_loop("win32") == "asyncio:SelectorEventLoop"
    assert loops.asyncio_loop_factory("win32") is asyncio.SelectorEventLoop


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_other_platforms_keep_their_defaults(platform: str) -> None:
    assert loops.uvicorn_loop(platform) == "auto"
    assert loops.asyncio_loop_factory(platform) is None


def test_serve_passes_the_app_factory_and_the_platform_loop(
    env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def record(*args: Any, **kwargs: Any) -> None:
        calls.append((args, kwargs))

    monkeypatch.setattr("uvicorn.run", record)
    assert cli.main(["serve", "--port", "8123"]) == 0
    assert calls == [
        (
            ("fource.server.main:app_factory",),
            {
                "factory": True,
                "host": "127.0.0.1",
                "port": 8123,
                "reload": False,
                "loop": loops.uvicorn_loop(),
            },
        )
    ]
