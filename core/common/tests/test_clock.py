from datetime import UTC, datetime

from fource.common import now, set_clock


def test_now_is_aware_utc() -> None:
    assert now().tzinfo is UTC


def test_the_clock_can_be_replaced_and_restored() -> None:
    fixed = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)
    set_clock(lambda: fixed)
    try:
        assert now() == fixed
    finally:
        set_clock(None)
    assert now() != fixed
