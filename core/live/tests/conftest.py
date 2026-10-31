import os
import uuid
from collections.abc import AsyncIterator

import pytest

from fource.live import Live, MemoryLive, RedisLive

NEEDS_REDIS = (
    "Redis tests need FOURCE_TEST_REDIS_URL: a Redis 8 server these tests may write to "
    "(CI's Redis job sets it). Never point it at a shared server."
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(params=["memory", pytest.param("redis", marks=pytest.mark.redis)])
async def live(request: pytest.FixtureRequest) -> AsyncIterator[Live]:
    """The same contract on both backends: this process's memory everywhere, and real Redis in
    CI's Redis job (`just test-redis`). The URL comes from the environment only, never .env.
    Each test gets its own key prefix, and every key it writes has a short time to live."""
    if request.param == "memory":
        yield MemoryLive()
        return
    url = os.environ.get("FOURCE_TEST_REDIS_URL")
    if not url:
        pytest.fail(NEEDS_REDIS)
    store = RedisLive(url, prefix=f"fource_test_{uuid.uuid4().hex[:12]}")
    try:
        yield store
    finally:
        await store.close()
