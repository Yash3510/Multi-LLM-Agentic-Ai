from collections.abc import AsyncIterator

import pytest

from fource.live import Live, MemoryLive


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(params=["memory"])
async def live(request: pytest.FixtureRequest) -> AsyncIterator[Live]:
    """Every contract test runs on each backend; Redis joins in the next task."""
    yield MemoryLive()
