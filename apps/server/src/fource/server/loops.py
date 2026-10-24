"""The event loop every server process uses."""

import asyncio
import sys
from collections.abc import Callable

# psycopg's async mode can't use the Proactor loop that Windows starts by default.


def uvicorn_loop(platform: str = sys.platform) -> str:
    return "asyncio:SelectorEventLoop" if platform == "win32" else "auto"


def asyncio_loop_factory(
    platform: str = sys.platform,
) -> Callable[[], asyncio.AbstractEventLoop] | None:
    return asyncio.SelectorEventLoop if platform == "win32" else None
