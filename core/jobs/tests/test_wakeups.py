import asyncio
import logging
import socket
from collections.abc import AsyncIterator
from typing import Any

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from sqlalchemy.engine import URL

from fource.jobs import listen_for_jobs

pytestmark = pytest.mark.anyio
PASSWORD = "not-the-real-password"


async def test_a_listener_that_cannot_connect_keeps_trying_until_stopped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    with socket.socket() as probe:  # a local port nothing listens on
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    url = f"postgresql+psycopg://fource_app:{PASSWORD}@127.0.0.1:{port}/fource"
    woken: list[bool] = []
    stop = asyncio.Event()
    listener = asyncio.create_task(
        listen_for_jobs(url, lambda: woken.append(True), stop, retry_seconds=0.05)
    )
    await asyncio.sleep(0.5)
    assert not listener.done()  # it is still trying, not gone
    stop.set()
    await asyncio.wait_for(listener, 10)
    assert woken == []
    assert "job wake-ups paused" in caplog.text and PASSWORD not in caplog.text


class FakeListener:
    """A connection that accepts LISTEN and never receives a notification."""

    async def __aenter__(self) -> "FakeListener":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def execute(self, query: str) -> None:
        return None

    async def notifies(self, *, timeout: float) -> AsyncIterator[object]:
        await asyncio.sleep(0.01)
        for _ in ():
            yield _


async def test_a_wake_up_that_raises_is_logged_by_class_and_the_listener_goes_on(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog.set_level(logging.WARNING)
    options: list[dict[str, object]] = []

    async def connect(conninfo: str, **given: object) -> FakeListener:
        options.append(given)
        return FakeListener()

    monkeypatch.setattr(psycopg.AsyncConnection, "connect", connect)
    calls: list[bool] = []
    second = asyncio.Event()

    def on_wake() -> None:
        calls.append(True)
        if len(calls) == 1:
            raise RuntimeError(f"postgresql://fource_app:{PASSWORD}@db/fource")
        second.set()

    stop = asyncio.Event()
    listener = asyncio.create_task(
        listen_for_jobs("postgresql+psycopg://u:p@h/d", on_wake, stop, retry_seconds=0.05)
    )
    await asyncio.wait_for(second.wait(), 10)
    assert not listener.done()
    stop.set()
    await asyncio.wait_for(listener, 10)
    assert "job wake-ups paused (RuntimeError)" in caplog.text and PASSWORD not in caplog.text
    assert options[0]["connect_timeout"] == 10


@pytest.mark.parametrize("as_url_object", [False, True])
async def test_the_password_reaches_the_connection_as_it_was_written(
    monkeypatch: pytest.MonkeyPatch, as_url_object: bool
) -> None:
    """A password with spaces or URI characters must not be re-rendered into a text that libpq
    refuses (job wake-ups would pause for good): connect with keyword arguments."""
    odd = "a b:c@d/e%f#g"
    url = URL.create("postgresql+psycopg", "fource_app", odd, "db.local", 5433, "fource")
    given: list[tuple[str, dict[str, Any]]] = []
    seen = asyncio.Event()

    async def connect(conninfo: str, **options: Any) -> FakeListener:
        given.append((conninfo, options))
        seen.set()
        return FakeListener()

    monkeypatch.setattr(psycopg.AsyncConnection, "connect", connect)
    stop = asyncio.Event()
    target = url if as_url_object else url.render_as_string(hide_password=False)
    listener = asyncio.create_task(listen_for_jobs(target, lambda: None, stop))
    await asyncio.wait_for(seen.wait(), 10)
    stop.set()
    await asyncio.wait_for(listener, 10)
    conninfo, options = given[0]
    assert odd not in conninfo  # never inside a rendered URI
    parsed = conninfo_to_dict(make_conninfo(conninfo, **options))
    assert (parsed["user"], parsed["password"], parsed["host"]) == ("fource_app", odd, "db.local")
    assert (parsed["port"], parsed["dbname"]) == ("5433", "fource")
