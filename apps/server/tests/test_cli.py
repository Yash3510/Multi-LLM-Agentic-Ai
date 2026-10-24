import asyncio
import json
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


def add_users(env: Path, monkeypatch: pytest.MonkeyPatch, *emails: str) -> None:
    cli.main(["migrate"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": PASSWORD)
    for email in emails:
        assert cli.main(["create-user", email, "--role", "Viewer"]) == 0


def test_keygen_writes_a_key_pair_once(env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["ledger", "keygen"]) == 0
    key = env.parent / "data" / "ledger" / "signing-key.pem"
    first = key.read_bytes()
    assert b"PRIVATE KEY" in first and (key.parent / "signing-key.pub.pem").is_file()
    out = capsys.readouterr().out
    assert "PRIVATE" not in out
    assert first.decode("ascii").splitlines()[1] not in out
    if os.name == "posix":
        assert key.stat().st_mode & 0o077 == 0
    assert cli.main(["ledger", "keygen"]) == 1
    assert key.read_bytes() == first


def test_the_key_file_can_be_set(
    env: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(tmp_path / "keys" / "ledger.pem"))
    assert cli.main(["ledger", "keygen"]) == 0
    assert (tmp_path / "keys" / "ledger.pem").is_file()
    assert (tmp_path / "keys" / "ledger.pub.pem").is_file()


def test_a_checkpoint_needs_the_key(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    assert cli.main(["ledger", "checkpoint"]) == 1
    assert "ledger keygen" in capsys.readouterr().out


def test_a_checkpoint_of_an_empty_ledger_is_refused(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["migrate"])
    cli.main(["ledger", "keygen"])
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    assert "no entries" in capsys.readouterr().out
    assert not (env.parent / "data" / "ledger" / "checkpoints").exists()


def test_checkpoint_then_verify(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com", "grace@example.com")
    cli.main(["ledger", "keygen"])
    assert cli.main(["ledger", "checkpoint"]) == 0
    saved = env.parent / "data" / "ledger" / "checkpoints" / "default-0000000002.json"
    assert json.loads(saved.read_text(encoding="utf-8"))["seq"] == 2
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 0
    out = capsys.readouterr().out
    assert "3 entries" in out and "up to entry 2" in out and "Verified." in out


def test_verify_finds_an_edit(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com", "grace@example.com")
    connection = sqlite3.connect(env)
    connection.execute("DROP TRIGGER ledger_entries_no_update")  # what only the owner can do
    connection.execute("UPDATE ledger_entries SET actor = 'anonymous' WHERE seq = 1")
    connection.commit()
    connection.close()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert "entry 1: altered" in out and "not proven" not in out


def test_verify_finds_a_cut_off_tail_only_with_a_checkpoint(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com", "grace@example.com")
    cli.main(["ledger", "keygen"])
    cli.main(["ledger", "checkpoint"])  # signs entry 2, and is entry 3
    connection = sqlite3.connect(env)
    connection.execute("DROP TRIGGER ledger_entries_no_delete")
    connection.execute("DELETE FROM ledger_entries WHERE seq >= 2")
    connection.commit()
    connection.close()
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert "entry 2: truncated" in out and "not proven" not in out
    empty = env.parent / "no-checkpoints"
    empty.mkdir()
    assert cli.main(["ledger", "verify", "--checkpoints", str(empty)]) == 0


def test_verify_fails_when_the_checkpoint_folder_is_missing(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    missing = env.parent / "usb-not-mounted"
    capsys.readouterr()
    assert cli.main(["ledger", "verify", "--checkpoints", str(missing)]) == 1
    out = capsys.readouterr().out
    assert f"No checkpoint folder at {missing}." in out and "Verified." not in out


def test_verify_says_when_nothing_anchors_the_chain(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 0
    out = capsys.readouterr().out
    assert "length is not proven" in out and "off the machine" in out
    assert "1 entry, head 1" in out and "1 entries" not in out


def test_verify_without_the_public_key_is_incomplete(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    cli.main(["ledger", "checkpoint"])
    (env.parent / "data" / "ledger" / "signing-key.pub.pem").unlink()
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 2
    out = capsys.readouterr().out
    assert "not checked" in out and "signing-key.pub.pem" in out
    assert "not proven" in out and "off the machine" not in out
    assert "2 signatures" in out and "1 signatures" not in out


def test_one_unchecked_signature_is_singular(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    cli.main(["ledger", "checkpoint"])
    (env.parent / "data" / "ledger" / "signing-key.pub.pem").unlink()
    empty = env.parent / "no-checkpoints"
    empty.mkdir()
    capsys.readouterr()
    assert cli.main(["ledger", "verify", "--checkpoints", str(empty)]) == 2
    out = capsys.readouterr().out
    assert "1 signature not checked" in out and "1 signatures" not in out


def test_a_checkpoint_file_is_never_overwritten(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    folder = env.parent / "data" / "ledger" / "checkpoints"
    folder.mkdir(parents=True)
    old = folder / "default-0000000001.json"
    old.write_text("kept\n", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert old.read_text(encoding="utf-8") == "kept\n"
    assert '"signature"' in out and "already exists" in out and "recorded" in out


def test_an_unreadable_checkpoint_file_is_reported(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    folder = env.parent / "checkpoints"
    (folder / "x.json").mkdir(parents=True)  # a directory cannot be read as a file
    capsys.readouterr()
    assert cli.main(["ledger", "verify", "--checkpoints", str(folder)]) == 1
    out = capsys.readouterr().out
    assert str(folder / "x.json") in out and "could not be read" in out
    assert "Verified." not in out


def test_a_default_checkpoint_folder_that_is_a_file_is_reported(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    folder = env.parent / "data" / "ledger" / "checkpoints"
    folder.parent.mkdir(parents=True)
    folder.write_text("not a folder", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert str(folder) in out and "could not be read" in out and "Verified." not in out


def test_keygen_names_the_file_that_is_in_the_way(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = env.parent / "data" / "ledger"
    folder.mkdir(parents=True)
    (folder / "signing-key.pub.pem").write_text("public", encoding="utf-8")
    assert cli.main(["ledger", "keygen"]) == 1
    assert "signing-key.pub.pem" in capsys.readouterr().out
    assert not (folder / "signing-key.pem").exists()


def make_unusable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not a key\n", encoding="utf-8")
    if os.name == "posix":
        path.chmod(0)  # unreadable; the file is also not a key, so a root user sees that


def test_an_unusable_private_key_is_named_and_not_shown(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "data" / "ledger" / "signing-key.pem"
    make_unusable(key)
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert str(key) in out and "Traceback" not in out and "not a key" not in out


def test_an_unusable_public_key_is_named(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "data" / "ledger" / "signing-key.pub.pem"
    make_unusable(key)
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert str(key) in out and "Verified." not in out
