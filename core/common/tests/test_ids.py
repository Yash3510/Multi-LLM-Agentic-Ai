import time
import uuid

from fource.common import new_id


def test_ids_are_version_7_with_the_standard_variant() -> None:
    value = new_id()
    assert value.version == 7
    assert value.variant == uuid.RFC_4122


def test_ids_made_in_a_row_are_already_in_order() -> None:
    ids = [new_id() for _ in range(10_000)]
    assert ids == sorted(ids)


def test_ids_carry_the_current_time_in_milliseconds() -> None:
    before = time.time_ns() // 1_000_000
    value = new_id()
    after = time.time_ns() // 1_000_000
    assert before <= value.int >> 80 <= after


def test_ids_are_unique() -> None:
    assert len({new_id() for _ in range(10_000)}) == 10_000
