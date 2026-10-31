import json
import os
import sqlite3
import uuid
from pathlib import Path

import pytest

from fource.ledger import load_private_key, sign_checkpoint
from fource.server import cli

PASSWORD = "correct horse battery"
EARLIER = "2026-01-01T00:00:00.000Z"


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A migrated SQLite database with a signing key in tmp_path, and scheduled checkpoints on.
    The key is a throwaway one made for this test."""
    monkeypatch.chdir(tmp_path)  # no .env from the repository
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)
    monkeypatch.setenv("FOURCE_SECRET_KEY", "s" * 40)
    database = tmp_path / "scheduled.db"
    monkeypatch.setenv("FOURCE_DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    monkeypatch.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "60")
    assert cli.main(["migrate"]) == 0
    assert cli.main(["ledger", "keygen"]) == 0
    return database


def folder(env: Path) -> Path:
    return env.parent / "data" / "ledger" / "checkpoints"


def add_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("getpass.getpass", lambda prompt="": PASSWORD)
    assert cli.main(["create-user", "ada@example.com", "--role", "Viewer"]) == 0


def first_entry(env: Path) -> tuple[str, str]:
    """The organisation (as entries name it) and hash of entry 1."""
    row = sqlite3.connect(env).execute("SELECT org_id, hash FROM ledger_entries WHERE seq = 1")
    org_hex, digest = row.fetchone()
    return str(uuid.UUID(org_hex)), digest


def jobs(env: Path) -> list[tuple[str, str, int, str | None]]:
    query = "SELECT kind, state, attempts, last_error FROM jobs ORDER BY created_at"
    return sqlite3.connect(env).execute(query).fetchall()


def test_the_worker_signs_the_head_and_the_chain_verifies(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_user(monkeypatch)
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 0
    assert "Ran 1 job attempt." in capsys.readouterr().out
    saved = folder(env) / "default-0000000001.json"
    assert json.loads(saved.read_text(encoding="utf-8"))["seq"] == 1
    assert cli.main(["worker", "--once"]) == 0  # the next one is an hour away
    assert "Ran 0 job attempts." in capsys.readouterr().out
    assert [file.name for file in folder(env).iterdir()] == ["default-0000000001.json"]
    assert [(kind, state) for kind, state, _, _ in jobs(env)] == [
        ("ledger.checkpoint", "done"),
        ("ledger.checkpoint", "queued"),
    ]
    assert cli.main(["ledger", "verify"]) == 0
    out = capsys.readouterr().out
    assert "2 entries" in out and "up to entry 1" in out and out.rstrip().endswith("\nVerified.")


def test_an_empty_ledger_is_not_signed(env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["worker", "--once"]) == 0
    assert not folder(env).exists()
    assert jobs(env) == [("ledger.checkpoint", "done", 1, None)]


def test_a_retry_keeps_the_file_it_wrote_for_the_same_entry(
    env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_user(monkeypatch)
    org, digest = first_entry(env)
    key = load_private_key(env.parent / "data" / "ledger" / "signing-key.pem")
    earlier = sign_checkpoint(key, org=org, seq=1, hash=digest, at=EARLIER)
    folder(env).mkdir(parents=True)
    saved = folder(env) / "default-0000000001.json"
    saved.write_text(json.dumps(earlier.to_dict()), encoding="utf-8")  # its commit then failed
    assert cli.main(["worker", "--once"]) == 0
    assert json.loads(saved.read_text(encoding="utf-8"))["at"] == EARLIER  # kept, not replaced
    assert jobs(env)[0][:2] == ("ledger.checkpoint", "done")
    assert cli.main(["ledger", "verify"]) == 0


def test_a_file_that_signs_another_entry_fails_the_attempt(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    add_user(monkeypatch)
    org, _ = first_entry(env)
    key = load_private_key(env.parent / "data" / "ledger" / "signing-key.pem")
    other = sign_checkpoint(key, org=org, seq=1, hash="f" * 64, at=EARLIER)
    folder(env).mkdir(parents=True)
    (folder(env) / "default-0000000001.json").write_text(json.dumps(other.to_dict()))
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 1  # a script or cron sees that the pass failed
    out = capsys.readouterr().out
    assert "Ran 1 job attempt." in out and "1 job attempt failed." in out
    [(kind, state, attempts, error)] = jobs(env)
    assert (kind, state, attempts) == ("ledger.checkpoint", "queued", 1)  # retried later
    assert error is not None and "may have been cut" in error
    count = sqlite3.connect(env).execute("SELECT count(*) FROM ledger_entries").fetchone()
    assert count == (1,)  # the checkpoint entry rolled back with the attempt
