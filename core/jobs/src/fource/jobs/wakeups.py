"""Waking workers when a job is queued: PostgreSQL's LISTEN/NOTIFY (ADR-0040).

SQLite has no notifications; there workers only poll.
"""

import asyncio
import logging
from collections.abc import Callable

import psycopg
from psycopg.conninfo import make_conninfo
from sqlalchemy.engine import URL, make_url

_log = logging.getLogger("fource.jobs")
_CONNECT_TIMEOUT = 10  # seconds: a host that does not answer must not hang the listener


async def _pause(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except TimeoutError:
        pass


def _conninfo(url: str | URL) -> str:
    """The URL's parts as libpq's keyword/value text, which psycopg quotes itself. A URI rendered
    from the URL would need every character of the password escaped, and one that libpq refuses
    (a space, say) would stop the wake-ups for good."""
    parts = make_url(url)
    given: dict[str, str | int | None] = {
        "host": parts.host,
        "port": parts.port,
        "user": parts.username,
        "password": parts.password,
        "dbname": parts.database,
    }
    for key, value in parts.query.items():
        given[key] = value if isinstance(value, str) else value[-1]
    return make_conninfo("", **{key: value for key, value in given.items() if value is not None})


async def listen_for_jobs(
    url: str | URL, on_wake: Callable[[], None], stop: asyncio.Event, *, retry_seconds: float = 5.0
) -> None:
    """Calls `on_wake` for every NOTIFY on the jobs channel until `stop` is set. The connection
    is the listener's own, in autocommit, so notifications arrive as soon as they are sent. If
    it drops, it is opened again after `retry_seconds`; the worker's polling covers the gap. Any
    other error (a failing `on_wake`, say) is logged and handled alike: the listener never ends
    on its own."""
    conninfo = _conninfo(url)
    while not stop.is_set():
        try:
            async with await psycopg.AsyncConnection.connect(
                conninfo, autocommit=True, connect_timeout=_CONNECT_TIMEOUT
            ) as listener:
                await listener.execute("LISTEN fource_jobs")
                on_wake()  # anything queued while nobody was listening
                while not stop.is_set():
                    async for _ in listener.notifies(timeout=1.0):
                        on_wake()
        except Exception as error:  # the class only: its text can name the host or the URL
            _log.warning("job wake-ups paused (%s); polling continues", type(error).__name__)
            await _pause(stop, retry_seconds)
