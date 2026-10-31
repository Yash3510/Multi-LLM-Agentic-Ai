import asyncio
import os
from pathlib import Path

import pytest

from fource.db import Database
from fource.jobs import Worker
from fource.server import cli
from fource.server.migrate import upgrade
from fource.server.worker import stop_handler

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
