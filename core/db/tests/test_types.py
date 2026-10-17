from datetime import UTC, datetime, timedelta, timezone

import pytest

from fource.db import UtcDateTime


def test_times_are_stored_as_utc_and_read_back_aware() -> None:
    column = UtcDateTime()
    india = timezone(timedelta(hours=5, minutes=30))
    stored = column.process_bind_param(datetime(2026, 10, 12, 15, 0, tzinfo=india), None)
    assert stored == datetime(2026, 10, 12, 9, 30)
    assert column.process_result_value(stored, None) == datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def test_a_time_without_a_zone_is_refused() -> None:
    with pytest.raises(ValueError):
        UtcDateTime().process_bind_param(datetime(2026, 10, 12, 12, 0), None)
