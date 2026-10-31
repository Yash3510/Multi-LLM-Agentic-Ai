"""Waking workers when a job is queued: PostgreSQL's LISTEN/NOTIFY (ADR-0040).

SQLite has no notifications; there workers only poll.
"""

import asyncio
import logging
from collections.abc import Callable

import psycopg
from sqlalchemy.engine import make_url

_log = logging.getLogger("fource.jobs")


async def _pause(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except TimeoutError:
        pass


async def listen_for_jobs(
    url: str, on_wake: Callable[[], None], stop: asyncio.Event, *, retry_seconds: float = 5.0
) -> None:
    """Calls `on_wake` for every NOTIFY on the jobs channel until `stop` is set. The connection
    is the listener's own, in autocommit, so notifications arrive as soon as they are sent. If
    it drops, it is opened again after `retry_seconds`; the worker's polling covers the gap."""
    conninfo = make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)
    while not stop.is_set():
        try:
            async with await psycopg.AsyncConnection.connect(conninfo, autocommit=True) as listener:
                await listener.execute("LISTEN fource_jobs")
                on_wake()  # anything queued while nobody was listening
                while not stop.is_set():
                    async for _ in listener.notifies(timeout=1.0):
                        on_wake()
        except (psycopg.Error, OSError) as error:  # the class only: its text can name the host
            _log.warning("job wake-ups paused (%s); polling continues", type(error).__name__)
            await _pause(stop, retry_seconds)
