"""Failing tests for the calibration tool, written before each fix."""

import asyncio
import importlib.util
from datetime import date
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parent / "tools" / "calibration.py"


@pytest.fixture(scope="module")
def cal():
    spec = importlib.util.spec_from_file_location("calibration_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cal, register: str, as_of: str = "2026-10-23", **valves) -> str:
    tool = cal.Tools()
    for name, value in valves.items():
        setattr(tool.valves, name, value)
    return asyncio.run(tool.check_calibration(register, as_of=as_of))


# 1. Unreadable as-found / tolerance is a finding, never "not recorded".

def test_bar_units_are_understood_and_compared(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| PG-101 | 2026-09-01 | 12 months | ±0.5 bar | +2.5 bar |"
    )
    out = run(cal, register)
    assert "OUT OF TOLERANCE" in out
    assert "not recorded" not in out


def test_an_unsupported_as_found_unit_is_unreadable_not_empty(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| PG-102 | 2026-09-01 | 12 months | ±0.5 widgets | +2.5 widgets |"
    )
    out = run(cal, register)
    assert "UNREADABLE" in out
    assert "CHECK INCOMPLETE" in out
    assert "widgets" in out


def test_an_unreadable_tolerance_alone_is_unreadable(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| PG-103 | 2026-09-01 | 12 months | ±0.5 widgets | |"
    )
    out = run(cal, register)
    assert "UNREADABLE" in out
    assert "CHECK INCOMPLETE" in out
    assert "widgets" in out


@pytest.mark.parametrize("unit", ["bar", "mbar", "Pa", "psig", "psia", "°F", "K", "kΩ"])
def test_common_units_are_parsed(cal, unit):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        f"| X-1 | 2026-09-01 | 12 months | ±2 {unit} | +1 {unit} |"
    )
    rows = cal.parse_table(register, True)
    assert rows and rows[0].tolerance is not None and rows[0].as_found is not None


# 2. semi-annual is six months, regardless of check order.

def test_semi_annual_is_six_months(cal):
    assert cal.parse_interval("semi-annual") == (6, 0)
    assert cal.parse_interval("semi annual") == (6, 0)
    assert cal.parse_interval("Semi-Annual") == (6, 0)
    assert cal.parse_interval("annual") == (12, 0)


# 3. A calibration dated after the reading cannot show what was valid then.

def test_a_calibration_after_the_reading_is_not_valid(cal):
    register = (
        "| Instrument | Last cal | Interval |\n"
        "|---|---|---|\n"
        "| TI-1 | 2026-03-10 | 12 months |"
    )
    out = run(cal, register, as_of="2026-03-05")
    assert "CAL AFTER READING" in out
    assert "CHECK INCOMPLETE" in out
    assert "previous calibration" in out.lower()


# 4. A stated due date later than the interval allows is not the due date.

def test_the_earlier_of_the_due_date_and_interval_wins(cal):
    register = (
        "| Instrument | Last cal | Interval | Due |\n"
        "|---|---|---|---|\n"
        "| TI-2 | 2026-01-01 | 12 months | 2027-06-01 |"
    )
    out = run(cal, register, as_of="2027-03-01")
    assert "OVERDUE" in out
    assert "ALL CURRENT" not in out
    assert "days from the date its interval gives" in out


# 5. Headings are matched as whole words, by specificity.

def test_manufacturer_is_not_an_uncertainty_column(cal):
    register = (
        "| Instrument | Last cal | Interval | Manufacturer |\n"
        "|---|---|---|---|\n"
        "| TI-3 | 2026-01-01 | 12 months | Acme |"
    )
    rows = cal.parse_table(register, True)
    assert rows and rows[0].uncertainty_text == ""
    assert rows[0].uncertainty is None


def test_as_left_error_does_not_become_as_found(cal):
    register = (
        "| Instrument | Last cal | Interval | As-left error |\n"
        "|---|---|---|---|\n"
        "| TI-4 | 2026-01-01 | 12 months | +0.2% FS |"
    )
    rows = cal.parse_table(register, True)
    assert rows and rows[0].as_found_text == ""
    assert rows[0].as_left_text == "+0.2% FS"


def test_next_cal_date_is_not_the_last_calibration(cal):
    register = (
        "| Instrument | Next cal date |\n"
        "|---|---|\n"
        "| TI-5 | 2027-01-01 |"
    )
    rows = cal.parse_table(register, True)
    assert rows and rows[0].last_cal is None
    assert rows[0].due == date(2027, 1, 1)


def test_reference_standard_id_is_not_an_instrument_column(cal):
    register = (
        "| Last cal | Ref standard ID | Due |\n"
        "|---|---|---|\n"
        "| 2026-01-01 | REF-9 | 2027-01-01 |"
    )
    assert cal.parse_table(register, True) == []


def test_valid_until_is_a_due_date(cal):
    register = (
        "| Instrument | Last cal | Valid until |\n"
        "|---|---|---|\n"
        "| TI-6 | 2026-01-01 | 2027-01-01 |"
    )
    rows = cal.parse_table(register, True)
    assert rows and rows[0].due == date(2027, 1, 1)


def test_headings_are_matched_whatever_their_order(cal):
    register = (
        "| As-found | Tolerance | Next cal date | Instrument |\n"
        "|---|---|---|---|\n"
        "| +0.2% FS | ±0.5% FS | 2027-01-01 | TI-7 |"
    )
    rows = cal.parse_table(register, True)
    assert rows
    inst = rows[0]
    assert inst.tag == "TI-7"
    assert inst.as_found is not None
    assert inst.tolerance is not None
    assert inst.due == date(2027, 1, 1)


# 6. Rows are not lost silently.

def test_a_blank_line_inside_a_table_does_not_end_it(cal):
    register = (
        "| Instrument | Last cal | Interval |\n"
        "|---|---|---|\n"
        "| A-1 | 2026-06-01 | 12 months |\n"
        "\n"
        "| B-1 | 2026-06-01 | 12 months |"
    )
    out = run(cal, register)
    assert "A-1" in out and "B-1" in out
    assert "2 rows read, 0 skipped" in out


def test_multiple_tables_are_read(cal):
    register = (
        "| Instrument | Last cal | Interval |\n"
        "|---|---|---|\n"
        "| A-1 | 2026-06-01 | 12 months |\n"
        "\n"
        "Some text between the tables.\n"
        "\n"
        "| Instrument | Last cal | Interval |\n"
        "|---|---|---|\n"
        "| B-1 | 2026-06-01 | 12 months |"
    )
    out = run(cal, register)
    assert "A-1" in out and "B-1" in out


def test_a_short_row_is_reported_not_dropped(cal):
    register = (
        "| Last cal | Interval | Instrument |\n"
        "|---|---|---|\n"
        "| 2026-06-01 | 12 months | A-1 |\n"
        "| 2026-06-01 |"
    )
    out = run(cal, register)
    assert "1 rows read, 1 skipped" in out
    assert "A-1" in out
    assert "line" in out
    assert "CHECK INCOMPLETE" in out


def test_an_unreadable_stated_due_date_prevents_an_all_clear(cal):
    register = (
        "| Instrument | Last cal | Interval | Due |\n"
        "|---|---|---|---|\n"
        "| A-1 | 2026-06-01 | 12 months | TBC |"
    )
    out = run(cal, register)
    assert "TBC" in out
    assert "CHECK INCOMPLETE" in out


def test_an_unreadable_date_is_named(cal):
    register = (
        "| Instrument | Last cal | Interval |\n"
        "|---|---|---|\n"
        "| A-1 | 31/04/2026 | 12 months |\n"
        "| B-1 | TBC | 12 months |"
    )
    out = run(cal, register)
    assert "31/04/2026" in out and "TBC" in out
    assert "could not be read" in out
    assert "Record the last calibration date and interval, or the due date" not in out


# 7. Ohm prefixes are case-sensitive; degrees allow a space.

def test_milli_and_mega_ohms_are_different(cal):
    assert cal.unit_kind("mΩ") == "mOhm"
    assert cal.unit_kind("MΩ") == "MOhm"
    assert cal.unit_kind("kΩ") == "kOhm"
    assert cal.unit_kind("Ω") == "Ohm"


def test_a_space_in_a_degree_unit_is_ignored(cal):
    assert cal.unit_kind("° C") == "°C"
    assert cal.unit_kind("° F") == "°F"


def test_ohms_with_different_prefixes_are_not_compared(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| TI-8 | 2026-09-01 | 12 months | ±5 MΩ | +6 mΩ |"
    )
    out = run(cal, register)
    assert "CHECK INCOMPLETE" in out
    assert "different unit" in out


# 8. The doubtful period for an as-found failure starts at the previous calibration.

def test_the_as_found_window_does_not_use_the_reading_date(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| TI-9 | 2026-06-01 | 12 months | ±0.5% FS | +0.8% FS |"
    )
    out = run(cal, register)
    assert "between 2026-06-01 and 2026-10-23" not in out
    assert "previous in-tolerance calibration" in out
    assert "date not in this register" in out
    assert "2026-06-01" in out


# 9. The status line counts what is actually current.

def test_the_status_count_excludes_failures_and_includes_due_soon(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found |\n"
        "|---|---|---|---|---|\n"
        "| A-1 | 2026-09-01 | 12 months | ±1% FS | +0.2% FS |\n"
        "| B-1 | 2025-10-01 | 12 months | ±1% FS | +0.2% FS |\n"
        "| C-1 | 2026-09-01 | 12 months | ±0.5% FS | +0.8% FS |\n"
        "| D-1 | 2026-09-01 | 12 months | ±0.5 widgets | +0.2 widgets |"
    )
    messages = []

    async def emit(message):
        messages.append(message)

    tool = cal.Tools()
    asyncio.run(tool.check_calibration(register, as_of="2026-09-25", __event_emitter__=emit))
    assert any("2/4 instruments current" in m["data"]["description"] for m in messages)


# 10. Prose and table rows apply the default interval under the same rule.

def test_prose_does_not_apply_a_default_interval_when_a_due_date_is_given(cal):
    inst = cal.parse_prose("Gauge PT-1 last calibrated 2026-01-01, due 2027-01-01.", True, 12)
    assert inst is not None
    assert inst.interval is None


def test_prose_applies_the_default_interval_when_no_due_date_exists(cal):
    inst = cal.parse_prose("Gauge PT-2 last calibrated 2026-01-01.", True, 12)
    assert inst is not None
    assert inst.interval == (12, 0)


# 11. A TUR that cannot be computed is said, not skipped.

def test_a_tur_unit_mismatch_is_reported(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found | Uncertainty |\n"
        "|---|---|---|---|---|---|\n"
        "| TI-10 | 2026-09-01 | 12 months | ±0.5% FS | +0.2% FS | 0.2 bar |"
    )
    out = run(cal, register)
    assert "uncertainty" in out.lower()
    assert "cannot be compared" in out


def test_a_zero_uncertainty_is_reported(cal):
    register = (
        "| Instrument | Last cal | Interval | Tolerance | As-found | Uncertainty |\n"
        "|---|---|---|---|---|---|\n"
        "| TI-11 | 2026-09-01 | 12 months | ±0.5% FS | +0.2% FS | 0% FS |"
    )
    out = run(cal, register)
    assert "zero" in out.lower()
