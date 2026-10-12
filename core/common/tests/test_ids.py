import time
import uuid

from fource.common import new_id


def test_ids_are_version_7_with_the_standard_variant() -> None:
    value = new_id()
    assert value.version == 7
    assert value.variant == uuid.RFC_4122


def test_ids_sort_by_creation_time() -> None:
    first = new_id()
    time.sleep(0.002)
    second = new_id()
    assert first < second


def test_ids_carry_the_current_time_in_milliseconds() -> None:
    before = time.time_ns() // 1_000_000
    value = new_id()
    after = time.time_ns() // 1_000_000
    assert before <= value.int >> 80 <= after


def test_ids_are_unique() -> None:
    assert len({new_id() for _ in range(10_000)}) == 10_000
