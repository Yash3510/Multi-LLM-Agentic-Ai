"""The worker process: `fource-server worker` (master plan §6.2, ADR-0040).

The same code as the server, a different role: it runs queued jobs. Today the only kind is
the scheduled ledger checkpoint, when FOURCE_LEDGER_CHECKPOINT_MINUTES is set.
"""

import asyncio
import signal
import sys
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy.exc import OperationalError, ProgrammingError

from fource.common import Settings
from fource.db import Database, table_missing
from fource.jobs import Handler, Recurring, Worker
from fource.ledger import UnusableKey, load_private_key
from fource.server.ledger_commands import key_file
from fource.server.main import UnsafeDatabaseRole, check_database_role
from fource.server.scheduled import CHECKPOINT, checkpoint_job

_NOT_SET_UP = "The database isn't set up yet: run `just migrate` first."


def _jobs(settings: Settings) -> tuple[dict[str, Handler], list[Recurring]] | str:
    """The jobs this worker runs, or why it can't start."""
    handlers: dict[str, Handler] = {}
    recurring: list[Recurring] = []
    if settings.ledger_checkpoint_minutes is not None:
        path = key_file(settings)
        try:
            private_key = load_private_key(path)
        except FileNotFoundError:
            return (
                f"Scheduled checkpoints are on, but there is no signing key at {path}: "
                "create one with `just ledger keygen`."
            )
        except OSError as error:
            return f"Could not read the ledger signing key at {path}: {error.strerror}."
        except UnusableKey as error:
            return str(error)
        every = timedelta(minutes=settings.ledger_checkpoint_minutes)
        handlers[CHECKPOINT], schedule = checkpoint_job(settings, private_key, every)
        recurring.append(schedule)
    return handlers, recurring


def stop_handler(worker: Worker, task: asyncio.Task[object]) -> Callable[[], None]:
    """What SIGINT and SIGTERM do: the first lets the running job finish, the second stops at
    once (that job's transaction rolls back and it is retried after its lease)."""
    received = 0

    def on_signal() -> None:
        nonlocal received
        received += 1
        if received == 1:
            print("Stopping after the running job; send the signal again to stop at once.")
            worker.stop()
        else:
            task.cancel()

    return on_signal


async def run_worker(settings: Settings, *, once: bool) -> int:
    jobs = _jobs(settings)
    if isinstance(jobs, str):
        print(jobs)
        return 1
    handlers, recurring = jobs
    database = Database(settings.database_url.get_secret_value())
    try:
        await check_database_role(database)
        worker = Worker(database, handlers, recurring=recurring)
        # run_once does not touch the database when nothing is scheduled, so look at it first: a
        # database that isn't set up fails here, at once, rather than idling.
        await database.org_id(settings.org)
        ran = await worker.run_once()
        if once:
            print(f"Ran {ran} job attempt{'' if ran == 1 else 's'}.")
            return 0
        task = asyncio.current_task()
        if task is not None and sys.platform != "win32":  # Windows: Ctrl+C stops at once
            loop = asyncio.get_running_loop()
            for each in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(each, stop_handler(worker, task))
        kinds = ", ".join(sorted(handlers)) or "none yet (scheduled checkpoints are off)"
        print(f"The worker is running. Kinds of job: {kinds}. Stop it with Ctrl+C.")
        await worker.run()
        return 0
    except UnsafeDatabaseRole as error:
        print(error.message)
        return 1
    except (OperationalError, ProgrammingError) as error:
        print(_NOT_SET_UP if table_missing(error) else f"Database error: {type(error).__name__}.")
        return 1
    finally:
        await database.dispose()
