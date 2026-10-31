import asyncio
import logging
import socket

import pytest

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
    stop.set()
    await asyncio.wait_for(listener, 10)
    assert woken == []
    assert "job wake-ups paused" in caplog.text and PASSWORD not in caplog.text
