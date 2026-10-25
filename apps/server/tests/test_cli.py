import asyncio
import base64
import json
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    PrivateFormat,
)
from sqlalchemy.exc import OperationalError, ProgrammingError

from fource.server import cli, loops
from fource.server.migrate import upgrade

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


def test_a_key_path_that_is_not_a_file_is_not_offered_keygen(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "key-is-a-folder"
    key.mkdir()
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert f"The ledger signing key path {key} is not a key file." in out
    assert "keygen" not in out


def test_a_key_path_that_is_a_dangling_link_is_not_offered_keygen(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "key-link.pem"
    if os.name == "posix":  # links need privileges on Windows
        key.symlink_to(env.parent / "usb-not-mounted")
    else:
        key.mkdir()
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert f"The ledger signing key path {key} is not a key file." in out
    assert "keygen" not in out


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
    assert "3 entries" in out and "up to entry 2" in out
    # Entry 3 is the checkpoint entry itself: there is nothing real after the anchor.
    assert "not covered" not in out and out.rstrip().endswith("\nVerified.")


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
    shown = str(folder.relative_to(env.parent))  # the default folder is relative to cwd
    assert shown in out and "could not be read" in out and "Verified." not in out


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
    assert str(key.relative_to(env.parent)) in out
    assert "Traceback" not in out and "not a key" not in out


def test_an_unusable_public_key_is_named(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "data" / "ledger" / "signing-key.pub.pem"
    make_unusable(key)
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert str(key.relative_to(env.parent)) in out and "Verified." not in out


@contextmanager
def unsearchable(folder: Path) -> Generator[None]:
    """A folder its owner may not search, so anything inside it can't even be looked up. Does
    nothing on Windows, and for root, who may search anything: the checks below then see a
    path that isn't there, which must fail just the same."""
    folder.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        folder.chmod(0)
    try:
        yield
    finally:
        if os.name == "posix":
            folder.chmod(0o700)


def test_an_unsearchable_checkpoint_folder_fails_cleanly(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    folder = env.parent / "locked" / "checkpoints"
    capsys.readouterr()
    with unsearchable(folder.parent):
        assert cli.main(["ledger", "verify", "--checkpoints", str(folder)]) == 1
    out = capsys.readouterr().out
    assert str(folder) in out and "Verified." not in out


def test_an_unsearchable_private_key_folder_fails_cleanly(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "locked" / "key.pem"
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    capsys.readouterr()
    with unsearchable(key.parent):
        assert cli.main(["ledger", "checkpoint"]) == 1
    assert str(key) in capsys.readouterr().out


def test_an_unsearchable_public_key_folder_fails_cleanly(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "locked" / "key.pub.pem"
    capsys.readouterr()
    with unsearchable(key.parent):
        assert cli.main(["ledger", "verify", "--public-key", str(key)]) == 1
    out = capsys.readouterr().out
    assert str(key) in out and "Verified." not in out


def test_an_unsearchable_default_public_key_folder_fails_cleanly(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(env.parent / "locked" / "key.pem"))
    capsys.readouterr()
    with unsearchable(env.parent / "locked"):
        code = cli.main(["ledger", "verify"])
    out = capsys.readouterr().out
    if os.name == "posix" and os.geteuid() != 0:
        assert code == 1 and "Could not read the public key" in out and "Verified." not in out
    else:  # the folder can still be searched, so the key is just missing: no crash, no failure
        assert code in {0, 1} and "Traceback" not in out


def pem(label: str, der_hex: str) -> bytes:
    body = base64.encodebytes(bytes.fromhex(der_hex)).decode("ascii")
    return f"-----BEGIN {label}-----\n{body}-----END {label}-----\n".encode("ascii")


# Well-formed key containers whose algorithm (OID 1.2.3.4) no library knows.
UNKNOWN_PUBLIC = pem("PUBLIC KEY", "300b300506032a0304030200aa")
UNKNOWN_PRIVATE = pem("PRIVATE KEY", "300d020100300506032a0304040100")


def test_a_private_key_of_an_unknown_type_is_not_a_usable_key(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "data" / "ledger" / "signing-key.pem"
    key.parent.mkdir(parents=True)
    key.write_bytes(UNKNOWN_PRIVATE)
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert str(key.relative_to(env.parent)) in out and "not a usable key" in out


def test_a_public_key_of_an_unknown_type_is_not_a_usable_key(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    given = env.parent / "given.pem"
    given.write_bytes(UNKNOWN_PUBLIC)
    default = env.parent / "data" / "ledger" / "signing-key.pub.pem"
    default.parent.mkdir(parents=True)
    default.write_bytes(UNKNOWN_PUBLIC)
    capsys.readouterr()
    for args in (["--public-key", str(given)], []):
        assert cli.main(["ledger", "verify", *args]) == 1
    out = capsys.readouterr().out
    assert str(given) in out and "not a usable key" in out and "Verified." not in out
    assert str(default.relative_to(env.parent)) in out


def test_a_short_key_path_does_not_let_the_parser_speak(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    (env.parent / "a").write_text("not a key\n", encoding="utf-8")
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", "a")  # "a" is part of any sentence
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    out = capsys.readouterr().out
    assert out.strip() == "a is not a usable key"
    assert "deserialize" not in out


def test_a_password_protected_key_is_still_named_as_such(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    key = env.parent / "data" / "ledger" / "signing-key.pem"
    key.parent.mkdir(parents=True)
    locked = Ed25519PrivateKey.generate().private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, BestAvailableEncryption(b"throwaway")
    )
    key.write_bytes(locked)
    capsys.readouterr()
    assert cli.main(["ledger", "checkpoint"]) == 1
    assert "password-protected" in capsys.readouterr().out


def test_a_deeply_nested_checkpoint_file_is_not_a_checkpoint(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    folder = env.parent / "checkpoints"
    folder.mkdir()
    (folder / "deep.json").write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["ledger", "verify", "--checkpoints", str(folder)]) == 1
    out = capsys.readouterr().out
    assert f"{folder / 'deep.json'} is not a checkpoint" in out and "Verified." not in out


def test_keygen_under_a_file_is_reported(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = env.parent / "afile"
    blocker.write_text("in the way", encoding="utf-8")
    key = blocker / "sub" / "key.pem"
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    assert cli.main(["ledger", "keygen"]) == 1
    assert f"Could not create the signing key at {key}:" in capsys.readouterr().out
    assert blocker.read_text(encoding="utf-8") == "in the way"


def test_keygen_in_a_folder_that_is_a_file_is_not_an_existing_key(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = env.parent / "afile"
    blocker.write_text("in the way", encoding="utf-8")
    key = blocker / "key.pem"  # the key folder is a file: creating it raises FileExistsError
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    assert cli.main(["ledger", "keygen"]) == 1
    out = capsys.readouterr().out
    assert f"Could not create the signing key at {key}:" in out
    assert "Not creating a signing key" not in out
    assert blocker.read_text(encoding="utf-8") == "in the way"


def test_keygen_in_an_unwritable_folder_leaves_nothing(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = env.parent / "readonly"
    folder.mkdir()
    key = folder / "key.pem"
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(key))
    if os.name == "posix":
        folder.chmod(0o500)
    try:
        code = cli.main(["ledger", "keygen"])
        created = sorted(folder.iterdir())
    finally:
        if os.name == "posix":
            folder.chmod(0o700)
    out = capsys.readouterr().out
    if os.name == "posix" and os.geteuid() != 0:
        assert code == 1 and created == [] and f"Could not create the signing key at {key}" in out


def test_a_default_checkpoint_folder_that_is_a_dangling_link_is_reported(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    folder = env.parent / "data" / "ledger" / "checkpoints"
    folder.parent.mkdir(parents=True)
    if os.name == "posix":  # links need privileges on Windows
        folder.symlink_to(env.parent / "usb-not-mounted")
    else:
        folder.write_text("stands in for a folder that can't be read", encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert "could not be read" in out and "Verified." not in out


def test_verify_warns_about_entries_no_checkpoint_covers(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com", "grace@example.com")
    cli.main(["ledger", "keygen"])
    cli.main(["ledger", "checkpoint"])  # signs entry 2, and is entry 3
    add_users(env, monkeypatch, "linus@example.com")  # entry 4, after the checkpoint
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 0
    out = capsys.readouterr().out
    assert "up to entry 2" in out
    assert "Entries after 2 are not covered by any checkpoint" in out
    assert "make a new checkpoint" in out
    last = out.rstrip().splitlines()[-1]
    assert last == ("Verified through entry 2; entries after it are not covered by any checkpoint.")


def test_verify_says_nothing_extra_when_nothing_is_anchored(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 0
    assert "not covered by any checkpoint" not in capsys.readouterr().out


def test_verify_reports_a_refs_cell_that_is_not_an_object(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_users(env, monkeypatch, "ada@example.com", "grace@example.com")
    connection = sqlite3.connect(env)
    connection.execute("DROP TRIGGER ledger_entries_no_update")
    connection.execute("UPDATE ledger_entries SET refs = '[1,2,3]' WHERE seq = 2")
    connection.commit()
    connection.close()
    capsys.readouterr()
    assert cli.main(["ledger", "verify"]) == 1
    out = capsys.readouterr().out
    assert "entry 2: altered" in out and "Failed." in out


@pytest.mark.parametrize("command", ["checkpoint", "verify"])
@pytest.mark.parametrize("revision", [None, "0003"])
def test_ledger_commands_on_a_database_without_the_ledger_say_it_is_not_set_up(
    env: Path, capsys: pytest.CaptureFixture[str], command: str, revision: str | None
) -> None:
    """Never migrated, or migrated before the ledger existed (a slice 1 install)."""
    if revision is not None:
        upgrade(f"sqlite+aiosqlite:///{env.as_posix()}", revision)
    cli.main(["ledger", "keygen"])
    capsys.readouterr()
    assert cli.main(["ledger", command]) == 1
    assert "just migrate" in capsys.readouterr().out


class DriverError(Exception):
    """What a driver's error carries: PostgreSQL's SQLSTATE."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__("driver text")
        self.sqlstate = sqlstate


@pytest.mark.parametrize("command", ["checkpoint", "verify"])
def test_a_missing_table_on_postgresql_is_also_not_set_up(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    """PostgreSQL reports it as a ProgrammingError with state 42P01, not an OperationalError."""
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    monkeypatch.setattr(
        f"fource.server.ledger_commands.{'verify_ledger' if command == 'verify' else 'checkpoint'}",
        raising(ProgrammingError("SELECT 1", None, DriverError("42P01"))),
    )
    capsys.readouterr()
    assert cli.main(["ledger", command]) == 1
    assert "just migrate" in capsys.readouterr().out


@pytest.mark.parametrize("command", ["checkpoint", "verify"])
@pytest.mark.parametrize("error", [ProgrammingError, OperationalError])
def test_any_other_database_error_is_named_without_a_traceback_or_the_url(
    env: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
    error: type[ProgrammingError | OperationalError],
) -> None:
    add_users(env, monkeypatch, "ada@example.com")
    cli.main(["ledger", "keygen"])
    monkeypatch.setattr(
        f"fource.server.ledger_commands.{'verify_ledger' if command == 'verify' else 'checkpoint'}",
        raising(error("SELECT 1", None, DriverError("42501"))),
    )
    capsys.readouterr()
    assert cli.main(["ledger", command]) == 1
    out = capsys.readouterr().out
    assert f"Could not read the database: {error.__name__}." in out
    assert "just migrate" not in out and "sqlite" not in out and "SELECT" not in out


def raising(error: Exception) -> Any:
    async def fail(*args: Any, **kwargs: Any) -> None:
        raise error

    return fail
