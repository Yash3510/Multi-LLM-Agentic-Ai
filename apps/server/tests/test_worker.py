import asyncio
import os
import signal
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

from fource.common import Settings
from fource.db import Database
from fource.jobs import Worker
from fource.server import cli
from fource.server.migrate import upgrade
from fource.server.worker import run_worker, stop_handler

pytestmark = pytest.mark.anyio


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)  # no .env from the repository
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # a shell's settings must never reach a real database
    monkeypatch.setenv("FOURCE_SECRET_KEY", "s" * 40)
    database = tmp_path / "worker.db"
    monkeypatch.setenv("FOURCE_DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    return database


def test_with_nothing_scheduled_the_worker_has_nothing_to_do(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["migrate"])
    assert cli.main(["worker", "--once"]) == 0
    assert "Ran 0 job attempts." in capsys.readouterr().out


def test_scheduled_checkpoints_need_the_signing_key(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["migrate"])
    monkeypatch.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "60")
    assert cli.main(["worker", "--once"]) == 1
    assert "just ledger keygen" in capsys.readouterr().out


def rsa_key() -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())


@pytest.mark.parametrize("kind", ["garbage", "rsa"])
def test_a_key_file_that_is_not_an_ed25519_key_is_refused_without_its_contents(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    cli.main(["migrate"])
    path = env.parent / "not-a-key.pem"
    if kind == "garbage":
        marker = "marker-4f1d9c-from-the-key-file"
        path.write_text(f"-----BEGIN PRIVATE KEY-----\n{marker}\n-----END PRIVATE KEY-----\n")
    else:
        content = rsa_key()
        path.write_bytes(content)
        marker = content.decode().splitlines()[1]  # a line of the key itself
    monkeypatch.setenv("FOURCE_LEDGER_KEY_FILE", str(path))
    monkeypatch.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "60")
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 1
    captured = capsys.readouterr()
    assert str(path) in captured.out  # says which file
    assert marker not in captured.out + captured.err  # never what is in it


def test_the_worker_on_a_database_that_is_not_set_up_says_so(
    env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["worker", "--once"]) == 1
    assert "just migrate" in capsys.readouterr().out


def test_the_worker_on_a_database_migrated_only_to_slice_2_says_so(
    env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # An install upgraded from slice 2 has orgs and the ledger but no jobs table. With scheduled
    # checkpoints on, a pass over it would fail again and again behind the worker's guard.
    upgrade(f"sqlite+aiosqlite:///{env.as_posix()}", "0004")
    monkeypatch.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "1")
    assert cli.main(["ledger", "keygen"]) == 0
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 1
    assert "just migrate" in capsys.readouterr().out


async def test_the_first_signal_lets_the_job_finish_and_the_second_stops_at_once(
    tmp_path: Path,
) -> None:
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'stop.db').as_posix()}")
    worker = Worker(database, {})
    task = asyncio.create_task(asyncio.sleep(30))
    on_signal = stop_handler(worker, task)
    on_signal()
    await asyncio.wait_for(worker.run(), 5)  # stopped: run() returns without a pass
    assert not task.done()
    on_signal()
    with pytest.raises(asyncio.CancelledError):
        await task
    await database.dispose()


async def test_the_stop_signals_are_handled_before_the_first_pass(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A SIGTERM during a long first pass used to kill the worker (exit 143) because the
    # handlers were installed after it. Nothing real is signalled: the loop's registration and
    # the first pass are spied on, in the order they happen.
    events: list[str] = []
    loop = asyncio.get_running_loop()

    def add_signal_handler(number: int, *_: object) -> None:
        events.append(signal.Signals(number).name)

    class Spied(Worker):
        async def run_once(self) -> int:
            events.append("pass")
            self.stop()  # one pass is enough: run() then returns at once
            return 0

    monkeypatch.setattr(loop, "add_signal_handler", add_signal_handler)
    monkeypatch.setattr("fource.server.worker.Worker", Spied)
    assert await run_worker(settings, once=False) == 0
    if sys.platform == "win32":  # no handlers there: Ctrl+C raises KeyboardInterrupt
        assert events == ["pass"]
    else:
        assert events == ["SIGINT", "SIGTERM", "pass"]
