"""
title: 4CE Instrument Calibration
author: 4CE
version: 0.1.0
description: Checks whether the instruments an inspection relied on were within their calibration date and tolerance at the date of the reading, and names the results a failed calibration puts in doubt. Date arithmetic and tolerance comparisons are performed locally, not judged by a model.
"""

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Awaitable, Callable

from pydantic import BaseModel, Field

_MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
_MONTHS.update({name.lower(): number for number, name in enumerate(calendar.month_abbr) if name})
_MONTHS["sept"] = 9

_DATE_TOKEN = (
    r"(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
    r"|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})"
)

# Longest alternatives first, so "mm/s" is not read as "mm" and "MOhm" not as
# "Ohm". A percentage is kept as its own kind because a tolerance given as a
# share of span cannot be compared with an error stated in engineering units.
_UNIT = (
    r"%\s*(?:of\s*)?(?:fs|span|full[\s-]?scale)?"
    r"|°\s*[cfk]"
    r"|deg(?:rees)?\s*[cfk]\b"
    r"|mm\s*/\s*s|mm\b"
    r"|mbar\b|bar\b|psig\b|psia\b|psi\b"
    r"|(?:k|m|M)?(?:ω|Ω|ohms?)\b"
    r"|kpa\b|mpa\b|hpa\b|\bpa\b"
    r"|\bma\b|\bmv\b|\bv\b|\bhz\b|rpm\b"
    r"|\bK\b"
)
_QUANTITY = re.compile(rf"([+-]?)\s*(\d+(?:\.\d+)?)\s*({_UNIT})", re.I)
_INTERVAL = re.compile(
    r"(\d+(?:\.\d+)?)\s*-?\s*(months?|mo\b|years?|yrs?|weeks?|days?"
    r"|annual|annually|yearly|quarterly|semi[\s-]?annual|monthly)",
    re.I,
)

_COLUMNS = {
    "instrument": (
        "instrument", "instrument tag", "tag no", "tag", "device", "gauge",
        "transmitter", "asset id", "asset", "id",
    ),
    "parameter": ("parameter", "service", "measurement", "function", "variable"),
    "last_cal": (
        "last calibration date", "last calibration", "last cal date", "last cal",
        "calibration date", "calibrated on", "calibrated", "cal date",
    ),
    "interval": (
        "recalibration interval", "calibration interval", "interval", "period",
        "frequency", "recalibration",
    ),
    "due": (
        "next calibration date", "next calibration", "next cal date", "next cal",
        "calibration due date", "calibration due", "valid until", "due date",
        "due", "expiry date", "expiry", "expires",
    ),
    "tolerance": ("acceptance tolerance", "tolerance", "accuracy", "acceptance", "permitted", "limit"),
    "as_found": ("as found error", "as found", "found error", "error"),
    "as_left": ("as left error", "as left"),
    "uncertainty": ("measurement uncertainty", "reference uncertainty", "uncertainty", "tur"),
    "certificate": ("certificate no", "certificate", "cert no", "cert", "report"),
}

# Headings that use a word from another column's vocabulary but are not that
# column. A reference standard's number is not the instrument, and a
# manufacturer's name is not a TUR.
_HEADER_REJECTS = {
    "instrument": ("ref", "reference", "standard", "manufacturer", "model", "serial", "certificate", "report"),
}


@dataclass
class Instrument:
    tag: str
    parameter: str = ""
    last_cal: date | None = None
    due: date | None = None
    interval: tuple[int, int] | None = None  # (months, days)
    tolerance: tuple[float, str] | None = None
    tolerance_text: str = ""
    as_found: tuple[float, str] | None = None
    as_found_text: str = ""
    as_left: tuple[float, str] | None = None
    as_left_text: str = ""
    uncertainty: tuple[float, str] | None = None
    uncertainty_text: str = ""
    certificate: str = ""
    notes: list[str] = field(default_factory=list)
    unreadable_dates: list[str] = field(default_factory=list)


@dataclass
class RegisterParse:
    instruments: list[Instrument] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    rows_read: int = 0
    from_table: bool = False


class Status(StrEnum):
    VALID = "VALID"
    DUE_SOON = "DUE SOON"
    PAST_DUE_GRACE = "PAST DUE (GRACE)"
    OVERDUE = "OVERDUE"
    NO_DATA = "NO DATA"
    CAL_AFTER_READING = "CAL AFTER READING"


class ToleranceVerdict(StrEnum):
    NOT_RECORDED = "NOT RECORDED"
    IN_TOLERANCE = "IN TOLERANCE"
    OUT_OF_TOLERANCE = "OUT OF TOLERANCE"
    NO_TOLERANCE = "NO TOLERANCE"
    NOT_COMPARABLE = "NOT COMPARABLE"
    UNREADABLE = "UNREADABLE"


@dataclass
class Assessment:
    tag: str
    parameter: str
    last_cal: date | None
    due: date | None
    status: Status
    status_text: str
    as_found_text: str
    tolerance: ToleranceVerdict
    action: str
    doubt: str
    notes: list[str]
    days: int | None
    unreadable_dates: list[str]


class Tools:
    class Valves(BaseModel):
        due_soon_days: int = Field(
            default=30,
            description="How many days before the due date an instrument is reported as due for recalibration.",
        )
        grace_days: int = Field(
            default=0,
            description="Days past the due date during which a documented extension is allowed. 0 means the due date is hard, and any day past it is overdue.",
        )
        default_interval_months: int = Field(
            default=0,
            description="Calibration interval used when a row states no interval and no due date. 0 leaves it unstated, which is reported as NO DATA rather than assumed.",
        )
        day_first: bool = Field(
            default=True,
            description="Read NN/NN/YYYY dates day-first, the plant convention here. Set false for month-first registers.",
        )
        tur_min: float = Field(
            default=4.0,
            description="The smallest test uncertainty ratio a calibration should hold: the tolerance divided by the reference standard's uncertainty. Below this the calibration itself is reported as too weak to prove the tolerance.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def check_calibration(
        self,
        register: str,
        as_of: str = "",
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Check instrument calibration dates and as-found errors, and name the readings a failed calibration puts in doubt.

        Use this whenever a reading is being relied on and its instrument's calibration matters: a gauge
        past its due date, a certificate with an as-found error outside tolerance, or any inspection whose
        verdict depends on a reading. Do not decide validity yourself - pass the register here, because the
        date arithmetic and the tolerance comparison are done locally and the result is reproducible.

        :param register: A calibration register as a table, or one instrument in a sentence. A table needs
            columns for the instrument and its calibration date or due date; optional columns are parameter,
            interval, tolerance, as-found error, as-left error, reference uncertainty and certificate.
            Column headings are matched loosely, so "Last cal", "Calibrated on" and "Cal. date" all work.
        :param as_of: The date the readings were taken, as YYYY-MM-DD, DD/MM/YYYY or "14 March 2026". Blank
            assesses against today. Pass the measurement date, not today, when asking whether an instrument
            was valid when a particular reading was recorded.
        :return: A table of instruments with their due date, status at the assessment date, as-found result
            and the action required, followed by the results a failed calibration puts in doubt and an
            overall disposition.
        """
        await _emit(__event_emitter__, "calibration", "Checking instrument calibration")

        text = (register or "").strip()
        if not text:
            await _emit(__event_emitter__, "calibration", "No register supplied", done=True)
            return (
                "No calibration register was supplied, so no instrument was checked. Pass the register as a "
                "table with the instrument, its last calibration date (or due date) and, where known, its "
                "interval, tolerance and as-found error."
            )

        when = date.today()
        if as_of.strip():
            parsed = parse_date(as_of.strip(), self.valves.day_first)
            if parsed is None:
                await _emit(__event_emitter__, "calibration", "Assessment date could not be read", done=True)
                return (
                    f"The assessment date `{as_of}` could not be read. Give it as YYYY-MM-DD, DD/MM/YYYY or "
                    '"14 March 2026". Nothing was assessed, because the wrong date would make every '
                    "validity answer wrong."
                )
            when = parsed

        report = parse_register_report(text, self.valves.day_first, self.valves.default_interval_months)
        instruments = report.instruments
        if not instruments:
            await _emit(__event_emitter__, "calibration", "No instruments found", done=True)
            message = (
                "No instruments could be read from that. Supply a table whose first line is a heading with "
                "an instrument column and a calibration-date or due-date column, and one row per instrument "
                "- for example: `| Instrument | Parameter | Last cal | Interval | Tolerance | As-found |`. "
                "Nothing was assessed rather than guessing which column meant what."
            )
            if report.from_table:
                message += "\n\n" + _skip_report(report)
            return message

        rows = [assess(instrument, when, self.valves) for instrument in instruments]

        out_of_tolerance = [row for row in rows if row.tolerance == ToleranceVerdict.OUT_OF_TOLERANCE]
        overdue = [row for row in rows if row.status == Status.OVERDUE]
        missing = [row for row in rows if row.status == Status.NO_DATA]
        unproven = [
            row for row in rows
            if row.tolerance in (
                ToleranceVerdict.NO_TOLERANCE,
                ToleranceVerdict.NOT_COMPARABLE,
                ToleranceVerdict.UNREADABLE,
            )
        ]
        cal_after_reading = [row for row in rows if row.status == Status.CAL_AFTER_READING]
        unreadable_dates = [row for row in rows if row.unreadable_dates]
        due_soon = [row for row in rows if row.status in (Status.DUE_SOON, Status.PAST_DUE_GRACE)]
        current = [
            row for row in rows
            if row.status in (Status.VALID, Status.DUE_SOON)
            and row.tolerance in (ToleranceVerdict.NOT_RECORDED, ToleranceVerdict.IN_TOLERANCE)
        ]

        if out_of_tolerance:
            disposition = "OUT OF TOLERANCE - RESULTS IN DOUBT"
        elif overdue:
            disposition = "OUT OF CALIBRATION - RESULTS IN DOUBT"
        elif missing or unproven or cal_after_reading or unreadable_dates or report.skipped:
            disposition = "CHECK INCOMPLETE"
        elif due_soon:
            disposition = "CALIBRATION DUE"
        else:
            disposition = "ALL CURRENT"

        await _emit(
            __event_emitter__,
            "calibration",
            f"{len(current)}/{len(rows)} instruments current",
            done=True,
        )

        lines = [
            f"## Calibration check - as of {when.isoformat()}",
            "",
            _headline(
                rows, out_of_tolerance, overdue, missing, unproven, cal_after_reading,
                unreadable_dates, len(report.skipped), due_soon,
            ),
            "",
            "| Instrument | Parameter | Last cal | Due | Status | As-found | Action |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in rows:
            lines.append(
                f"| {row.tag} | {row.parameter or '-'} | {_iso(row.last_cal)} | {_iso(row.due)} "
                f"| {row.status_text} | {row.as_found_text} | {row.action} |"
            )

        if report.from_table:
            lines += ["", _skip_report(report)]
            if report.skipped:
                lines += [""] + [f"- {reason}" for reason in report.skipped]

        actions = [row for row in rows if row.action]
        if actions:
            lines += ["", "### Required actions", ""]
            for row in actions:
                lines.append(f"- **{row.tag}** - {row.action}")

        if out_of_tolerance or overdue:
            lines += ["", "### Results in doubt", ""]
            seen: set[str] = set()
            for row in out_of_tolerance + overdue:
                if row.tag in seen or not row.doubt:
                    continue
                seen.add(row.tag)
                lines.append(f"- **{row.tag}** - {row.doubt}")

        notes = [note for row in rows for note in row.notes]
        if notes:
            lines += ["", "### Register notes", ""]
            for note in notes:
                lines.append(f"- {note}")

        lines += [
            "",
            f"**Disposition: {disposition}**",
        ]
        if out_of_tolerance:
            lines.append(
                "\n> An as-found error outside tolerance means the instrument was wrong while its calibration "
                "was still current. The results it produced inside the look-back windows above cannot be "
                "released on their own evidence; an out-of-tolerance record and an impact assessment are "
                "required before they are used again."
            )
        elif overdue:
            lines.append(
                "\n> A lapsed calibration is not a finding about the instrument's accuracy - nothing has been "
                "measured to show it wrong. It is a finding about the evidence: readings taken after the due "
                "date have no calibration behind them and cannot be relied on until the instrument is "
                "recalibrated."
            )
        if missing:
            lines.append(
                "\n> One or more instruments could not be placed in time, so this is not an all-clear. Supply "
                "the missing last-calibration date or interval and re-run before releasing the readings."
            )
        if self.valves.grace_days:
            lines.append(
                f"\n*An extension of up to {self.valves.grace_days} days past the due date is allowed by the "
                "configuration. A reading inside that window is reported as PAST DUE (GRACE), not valid, and "
                "the extension must be authorised and recorded.*"
            )

        lines.append(
            f"\n*Assessed at {when.isoformat()} against the dates and tolerances supplied. Due dates are the "
            "stated due date, or the last calibration plus the stated interval. The comparison is arithmetic "
            "performed on this machine - no model judged whether an instrument was in tolerance. An in-date "
            "instrument can still fail as-found; a current sticker does not prove the readings were right.*"
        )
        return "\n".join(lines)


def assess(instrument: Instrument, when: date, valves: "Tools.Valves") -> Assessment:
    """Place one instrument in time and compare its as-found error with its tolerance."""
    notes = list(instrument.notes)

    computed_due = None
    if instrument.last_cal and instrument.interval:
        computed_due = add_offset(instrument.last_cal, *instrument.interval)
    if instrument.due and computed_due and abs((instrument.due - computed_due).days) > 1:
        notes.append(
            f"{instrument.tag}: the register's due date {instrument.due.isoformat()} is "
            f"{abs((instrument.due - computed_due).days)} days from the date its interval gives "
            f"({computed_due.isoformat()}). One of the two is wrong and the register should be corrected."
        )

    # When the stated due date and the interval disagree, the earlier date is
    # the one that can be defended: the instrument cannot be assumed current
    # beyond the first of the two.
    if instrument.due and computed_due and abs((instrument.due - computed_due).days) > 1:
        due = min(instrument.due, computed_due)
    else:
        due = instrument.due or computed_due

    status, status_text, action = Status.NO_DATA, "NO DATA", ""
    days = None
    if due is None:
        if instrument.unreadable_dates:
            missing = " and ".join(dict.fromkeys(instrument.unreadable_dates))
            action = f"Supply a readable {missing} before relying on a reading."
        else:
            action = (
                "Record the last calibration date and interval, or the due date, before relying on a reading."
            )
    else:
        days = (due - when).days
        grace = max(0, valves.grace_days)
        if days < -grace:
            status = Status.OVERDUE
            status_text = f"OVERDUE ({abs(days)} d past)"
            action = (
                f"Remove from service and recalibrate. Readings taken after {due.isoformat()} have no "
                "calibration behind them."
            )
        elif days < 0:
            status = Status.PAST_DUE_GRACE
            status_text = f"PAST DUE ({abs(days)} d, in grace)"
            action = (
                f"Calibration expired {due.isoformat()}. Authorise and record the extension, and recalibrate "
                "before the next reading."
            )
        elif days <= max(0, valves.due_soon_days):
            status = Status.DUE_SOON
            status_text = f"DUE SOON ({days} d)"
            action = f"Schedule recalibration before {due.isoformat()}."
        else:
            status = Status.VALID
            status_text = f"VALID ({days} d)"

    if instrument.last_cal and instrument.last_cal > when:
        later = (instrument.last_cal - when).days
        status = Status.CAL_AFTER_READING
        status_text = f"CAL AFTER READING (last cal {instrument.last_cal.isoformat()}, {later} d after)"
        action = (
            f"Supply the previous calibration, the one in force on {when.isoformat()}; the "
            f"{instrument.last_cal.isoformat()} calibration was performed after the reading and "
            "cannot show what was valid then."
        )

    tolerance_verdict = ToleranceVerdict.NOT_RECORDED
    if instrument.as_found is not None:
        as_found_text = instrument.as_found_text or _quantity_text(instrument.as_found)
    elif instrument.as_found_text:
        as_found_text = instrument.as_found_text
    else:
        as_found_text = "not recorded"
    doubt = ""

    unreadable: list[tuple[str, str]] = []
    if instrument.as_found_text and instrument.as_found is None:
        unreadable.append(("as-found error", instrument.as_found_text))
    if instrument.tolerance_text and instrument.tolerance is None:
        unreadable.append(("tolerance", instrument.tolerance_text))
    if unreadable:
        tolerance_verdict = ToleranceVerdict.UNREADABLE
        as_found_text = f"{as_found_text} (unreadable)"
        status_text = f"{status_text}, UNREADABLE"
        for name, raw in unreadable:
            notes.append(
                f"{instrument.tag}: the {name} '{raw}' could not be read; give a number with a "
                "recognised unit (for example ±0.5% FS or ±2 °C)."
            )
        action = (
            (action + " " if action else "")
            + "State the as-found error and the tolerance with recognised units so the acceptance can be checked."
        )
    elif instrument.as_found is not None and instrument.tolerance is None:
        tolerance_verdict = ToleranceVerdict.NO_TOLERANCE
        as_found_text = f"{as_found_text} (no tolerance to compare)"
        action = (
            (action + " " if action else "")
            + "Record the acceptance tolerance so the as-found result can be checked."
        )
    elif instrument.as_found is not None and instrument.tolerance is not None:
        found_value, found_kind = instrument.as_found
        limit, limit_kind = instrument.tolerance
        if found_kind != limit_kind:
            tolerance_verdict = ToleranceVerdict.NOT_COMPARABLE
            action = (
                (action + " " if action else "")
                + "State the tolerance and the as-found error in the same unit so the acceptance can be checked."
            )
            notes.append(
                f"{instrument.tag}: the tolerance is in {limit_kind} and the as-found error in {found_kind}. "
                "They cannot be compared - state both in the same unit, or the acceptance check cannot be made."
            )
        elif abs(found_value) > abs(limit) + 1e-9:
            tolerance_verdict = ToleranceVerdict.OUT_OF_TOLERANCE
            if instrument.last_cal:
                window = f"up to the as-found calibration on {instrument.last_cal.isoformat()}"
            else:
                window = "up to the as-found calibration (date not in this register)"
            doubt = (
                f"as-found {as_found_text} against {instrument.tolerance_text}; the doubtful window runs "
                f"from the previous in-tolerance calibration (date not in this register) {window}. "
                "Supply that previous date to bound the impact assessment."
            )
        else:
            tolerance_verdict = ToleranceVerdict.IN_TOLERANCE

        if (
            tolerance_verdict in (ToleranceVerdict.IN_TOLERANCE, ToleranceVerdict.OUT_OF_TOLERANCE)
            and instrument.as_left is not None
        ):
            left_value, left_kind = instrument.as_left
            if left_kind == limit_kind and abs(left_value) <= abs(limit) + 1e-9:
                if tolerance_verdict == ToleranceVerdict.IN_TOLERANCE and not action:
                    action = "Return to service: as-left is within tolerance."
                else:
                    notes.append(
                        f"{instrument.tag}: as-left {instrument.as_left_text or _quantity_text(instrument.as_left)} "
                        "is within tolerance, so it may return to service once the results above are dispositioned."
                    )
            else:
                notes.append(
                    f"{instrument.tag}: as-left {instrument.as_left_text or _quantity_text(instrument.as_left)} "
                    "is not shown within tolerance, so it has not been returned to service by this record."
                )

    if status == Status.OVERDUE and not doubt:
        doubt = (
            f"no calibration was current between {due.isoformat()} and {when.isoformat()}, so any reading "
            "taken in that window has no calibration behind it."
        )

    if instrument.uncertainty_text and instrument.uncertainty is None:
        notes.append(
            f"{instrument.tag}: the reference uncertainty '{instrument.uncertainty_text}' could not be "
            "read, so the TUR was not computed."
        )
    if instrument.uncertainty is not None and instrument.tolerance is not None:
        uncertainty_value, uncertainty_kind = instrument.uncertainty
        limit, limit_kind = instrument.tolerance
        if uncertainty_kind != limit_kind:
            notes.append(
                f"{instrument.tag}: the uncertainty is in {uncertainty_kind} and the tolerance in "
                f"{limit_kind}; the TUR cannot be compared until both are in the same unit."
            )
        elif uncertainty_value == 0:
            notes.append(
                f"{instrument.tag}: the reference standard's uncertainty is zero, so the TUR cannot be "
                "computed; a zero-uncertainty reference cannot prove the tolerance."
            )
        else:
            ratio = abs(limit) / abs(uncertainty_value)
            if ratio < valves.tur_min:
                notes.append(
                    f"{instrument.tag}: the reference standard's uncertainty is {ratio:.1f}:1 against the "
                    f"tolerance, below the {valves.tur_min:g}:1 a calibration should hold. The pass or fail "
                    "is weaker than it looks."
                )

    if tolerance_verdict == ToleranceVerdict.OUT_OF_TOLERANCE and status != Status.OVERDUE:
        status_text = f"{status_text}, as-found OOT"
    if tolerance_verdict == ToleranceVerdict.OUT_OF_TOLERANCE:
        compared_with = instrument.tolerance_text or _quantity_text(instrument.tolerance)
        as_found_text = f"{as_found_text} (outside {compared_with})"
        if status == Status.OVERDUE:
            record = "Raise an out-of-tolerance record and assess every result produced since the last in-tolerance check."
        else:
            record = (
                "Raise an out-of-tolerance record, remove the instrument from service, and assess every "
                "result produced since the last in-tolerance check."
            )
        action = (action + " " if action else "") + record
    elif tolerance_verdict == ToleranceVerdict.IN_TOLERANCE:
        as_found_text = f"{as_found_text} (within {instrument.tolerance_text or _quantity_text(instrument.tolerance)})"
    elif tolerance_verdict == ToleranceVerdict.NOT_COMPARABLE:
        as_found_text = f"{as_found_text} (tolerance in a different unit)"

    return Assessment(
        tag=instrument.tag,
        parameter=instrument.parameter,
        last_cal=instrument.last_cal,
        due=due,
        status=status,
        status_text=status_text,
        as_found_text=as_found_text,
        tolerance=tolerance_verdict,
        action=action,
        doubt=doubt,
        notes=notes,
        days=days,
        unreadable_dates=instrument.unreadable_dates,
    )


def parse_register(text: str, day_first: bool, default_interval_months: int = 0) -> list[Instrument]:
    return parse_register_report(text, day_first, default_interval_months).instruments


def parse_register_report(
    text: str, day_first: bool, default_interval_months: int = 0
) -> RegisterParse:
    """Read every register table, and say what could not be read."""
    report = parse_table_report(text, day_first, default_interval_months)
    if report.instruments or report.from_table:
        return report
    prose = parse_prose(text, day_first, default_interval_months)
    if prose:
        return RegisterParse(instruments=[prose])
    return report


def parse_table(text: str, day_first: bool, default_interval_months: int = 0) -> list[Instrument]:
    return parse_table_report(text, day_first, default_interval_months).instruments


def _is_separator(line: str) -> bool:
    return bool(re.match(r"^\|?\s*:?-{2,}", line.strip()))


def _normalise_header(value: str) -> str:
    value = value.lower().replace("-", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _header_rank(header: str, phrase: str) -> tuple[int, int, int] | None:
    """How specifically a heading matches a column phrase: exact, edge, or word."""
    if header == phrase:
        return (3, len(phrase.split()), len(phrase))
    if header.startswith(phrase + " ") or header.endswith(" " + phrase):
        return (2, len(phrase.split()), len(phrase))
    if f" {phrase} " in f" {header} ":
        return (1, len(phrase.split()), len(phrase))
    return None


def match_columns(header: list[str]) -> dict[str, int]:
    """Assign each heading to at most one column, most specific match first."""
    candidates: list[tuple[tuple[int, int, int], str, int]] = []
    for key, phrases in _COLUMNS.items():
        rejects = _HEADER_REJECTS.get(key, ())
        for position, name in enumerate(header):
            if any(re.search(rf"\b{re.escape(word)}\b", name) for word in rejects):
                continue
            best = None
            for phrase in phrases:
                rank = _header_rank(name, phrase)
                if rank is not None and (best is None or rank > best):
                    best = rank
            if best is not None:
                candidates.append((best, key, position))

    candidates.sort(key=lambda candidate: candidate[0], reverse=True)
    columns: dict[str, int] = {}
    used: set[int] = set()
    for _, key, position in candidates:
        if key in columns or position in used:
            continue
        columns[key] = position
        used.add(position)
    return columns


def parse_table_report(
    text: str, day_first: bool, default_interval_months: int = 0
) -> RegisterParse:
    lines = text.splitlines()
    report = RegisterParse()
    index = 0
    while index < len(lines) - 1:
        if not (lines[index].strip().startswith("|") and _is_separator(lines[index + 1])):
            index += 1
            continue
        report.from_table = True
        header = [_normalise_header(cell) for cell in lines[index].strip().strip("|").split("|")]
        columns = match_columns(header)
        if "instrument" not in columns or not ({"last_cal", "due"} & set(columns)):
            report.skipped.append(
                f"line {index + 1}: table skipped - it has no instrument column and calibration date or due date."
            )
            index += 1
            continue

        position = index + 2
        while position < len(lines):
            raw = lines[position]
            line = raw.strip()
            if not line:
                position += 1
                continue
            if not line.startswith("|"):
                break
            if position + 1 < len(lines) and _is_separator(lines[position + 1]):
                break
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) <= columns["instrument"]:
                report.skipped.append(
                    f"line {position + 1}: {len(cells)} cell(s), but the instrument column is "
                    f"{columns['instrument'] + 1}."
                )
                position += 1
                continue
            tag = re.sub(r"[*_`]", "", cells[columns["instrument"]]).strip()
            if not tag or re.fullmatch(r"[-: ]+", tag):
                report.skipped.append(f"line {position + 1}: no instrument tag.")
                position += 1
                continue
            report.instruments.append(
                _instrument_from_cells(tag, cells, columns, day_first, default_interval_months)
            )
            position += 1
        index = max(position, index + 1)

    report.rows_read = len(report.instruments)
    return report


def _skip_report(report: RegisterParse) -> str:
    return f"**{report.rows_read} rows read, {len(report.skipped)} skipped.**"


def _instrument_from_cells(
    tag: str, cells: list[str], columns: dict[str, int], day_first: bool, default_interval_months: int
) -> Instrument:
    def cell(key: str) -> str:
        position = columns.get(key)
        return cells[position].strip() if position is not None and position < len(cells) else ""

    instrument = Instrument(tag=tag, parameter=cell("parameter"))

    last_cal_text = cell("last_cal")
    instrument.last_cal = first_date(last_cal_text, day_first)
    if last_cal_text and instrument.last_cal is None:
        instrument.unreadable_dates.append("last calibration date")
        instrument.notes.append(
            f"{tag}: the last calibration date '{last_cal_text}' could not be read; give a real date."
        )

    due_text = cell("due")
    instrument.due = first_date(due_text, day_first)
    if due_text and instrument.due is None:
        instrument.unreadable_dates.append("due date")
        instrument.notes.append(f"{tag}: the due date '{due_text}' could not be read; give a real date.")

    interval_text = cell("interval")
    instrument.interval = parse_interval(interval_text)
    if interval_text and instrument.interval is None:
        instrument.notes.append(
            f"{tag}: the interval '{interval_text}' could not be read; state it in months or days."
        )
    if instrument.interval is None and not instrument.due and default_interval_months > 0:
        instrument.interval = (int(default_interval_months), 0)
    instrument.tolerance_text = cell("tolerance")
    instrument.tolerance = parse_quantity(instrument.tolerance_text)
    instrument.as_found_text = cell("as_found")
    instrument.as_found = parse_quantity(instrument.as_found_text)
    instrument.as_left_text = cell("as_left")
    instrument.as_left = parse_quantity(instrument.as_left_text)
    instrument.uncertainty_text = cell("uncertainty")
    instrument.uncertainty = parse_quantity(instrument.uncertainty_text)
    instrument.certificate = cell("certificate")
    return instrument


def parse_prose(text: str, day_first: bool, default_interval_months: int = 0) -> Instrument | None:
    """One instrument described in a sentence, rather than a register table."""
    dates = [parsed for token in re.findall(_DATE_TOKEN, text) if (parsed := parse_date(token, day_first))]

    last_cal = _labelled_date(text, r"(?:last\s+calibrated|last\s+calibration|calibrated\s+on|cal\.?\s*date)", day_first)
    due = _labelled_date(text, r"(?:next\s+calibration|calibration\s+due|\bdue\b|expires?)", day_first)
    interval = parse_interval(text)
    if interval is None and due is None and default_interval_months > 0:
        interval = (int(default_interval_months), 0)

    if last_cal is None and due is None:
        # A single unlabelled date beside an interval is the calibration date.
        if len(dates) == 1 and interval:
            last_cal = dates[0]
        else:
            return None

    tag = ""
    labelled = re.search(
        r"(?:instrument|tag|device|gauge|transmitter|sensor)\s*(?:id|no\.?|number|#)?\s*[:=]?\s*"
        r"([A-Z]{1,4}[- ]?\d{1,4}[A-Z]?)",
        text,
        re.I,
    )
    if labelled:
        tag = re.sub(r"\s+", "-", labelled.group(1).strip().upper())
    else:
        bare = re.search(r"\b([A-Z]{1,4}-\d{1,4}[A-Z]?)\b", text)
        tag = bare.group(1) if bare else "instrument"
    if "-" not in tag and re.fullmatch(r"[A-Z]{1,4}\d{1,4}[A-Z]?", tag):
        tag = re.sub(r"^([A-Z]{1,4})(\d)", r"\1-\2", tag)

    parameter = ""
    described = re.search(
        r"(?:parameter|measures|measuring|service|function)\s*[:=]?\s*([A-Za-z][^,;.\n]{1,40})", text, re.I
    )
    if described:
        parameter = described.group(1).strip()

    instrument = Instrument(
        tag=tag,
        parameter=parameter,
        last_cal=last_cal,
        due=due,
        interval=interval,
    )
    instrument.tolerance_text = _labelled_quantity(text, r"tol(?:erance)?")
    instrument.tolerance = parse_quantity(instrument.tolerance_text)
    instrument.as_found_text = _labelled_quantity(text, r"as[\s-]?found(?:\s+error)?")
    instrument.as_found = parse_quantity(instrument.as_found_text)
    instrument.as_left_text = _labelled_quantity(text, r"as[\s-]?left(?:\s+error)?")
    instrument.as_left = parse_quantity(instrument.as_left_text)
    instrument.uncertainty_text = _labelled_quantity(text, r"(?:reference\s+)?uncertainty")
    instrument.uncertainty = parse_quantity(instrument.uncertainty_text)
    certificate = re.search(r"cert(?:ificate)?\s*(?:no\.?|number|#)?\s*[:=]?\s*([A-Z0-9][A-Z0-9/-]{2,})", text, re.I)
    if certificate:
        instrument.certificate = certificate.group(1)
    return instrument


def _labelled_date(text: str, label: str, day_first: bool) -> date | None:
    found = re.search(rf"{label}\s*(?:on|date)?\s*[:=]?\s*{_DATE_TOKEN}", text, re.I)
    if not found:
        return None
    token = re.search(_DATE_TOKEN, found.group(0))
    return parse_date(token.group(0), day_first) if token else None


def _labelled_quantity(text: str, label: str) -> str:
    found = re.search(
        rf"({label}\s*(?:error)?\s*[:=]?\s*(?:±|\+/-)?\s*{_QUANTITY.pattern})", text, re.I
    )
    if not found:
        return ""
    quantity = re.search(rf"(?:±|\+/-)?\s*{_QUANTITY.pattern}", found.group(1), re.I)
    return quantity.group(0).strip() if quantity else ""


def parse_date(text: str, day_first: bool = True) -> date | None:
    value = re.sub(r"\s+", " ", (text or "").strip()).replace(",", "")
    if not value:
        return None

    iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", value)
    if iso:
        return _make_date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))

    numeric = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", value)
    if numeric:
        first, second = int(numeric.group(1)), int(numeric.group(2))
        year = int(numeric.group(3))
        year = year + 2000 if year < 100 else year
        if day_first and second <= 12:
            return _make_date(year, second, first)
        if first > 12 and second <= 12:
            return _make_date(year, second, first)
        return _make_date(year, first, second)

    day_name = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\.?\s+(\d{4})$", value)
    if day_name:
        month = _MONTHS.get(day_name.group(2).lower())
        return _make_date(int(day_name.group(3)), month, int(day_name.group(1))) if month else None

    name_day = re.match(r"^([A-Za-z]+)\.?\s+(\d{1,2})\s+(\d{4})$", value)
    if name_day:
        month = _MONTHS.get(name_day.group(1).lower())
        return _make_date(int(name_day.group(3)), month, int(name_day.group(2))) if month else None

    return None


def first_date(text: str, day_first: bool = True) -> date | None:
    for token in re.findall(_DATE_TOKEN, text or ""):
        parsed = parse_date(token, day_first)
        if parsed:
            return parsed
    return None


def _make_date(year: int, month: int | None, day: int) -> date | None:
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_interval(text: str) -> tuple[int, int] | None:
    """An interval as (months, days), so a due date can be computed month-aware."""
    value = (text or "").strip()
    if not value:
        return None

    words = {
        "annual": (12, 0), "annually": (12, 0), "yearly": (12, 0),
        "quarterly": (3, 0), "semi-annual": (6, 0), "semi annual": (6, 0),
        "monthly": (1, 0),
    }
    lowered = re.sub(r"\s+", " ", value.lower())
    # Longest phrase first, and a hyphen is part of the word, so "annual"
    # cannot match inside "semi-annual" whatever order the dict is in.
    for word, offset in sorted(words.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lowered):
            return offset

    found = _INTERVAL.search(lowered)
    if found:
        amount = float(found.group(1))
        unit = found.group(2)
        if unit.startswith(("year", "yr")):
            return (round(amount * 12), 0)
        if unit.startswith("week"):
            return (0, round(amount * 7))
        if unit.startswith("day"):
            return (0, round(amount))
        return (round(amount), 0)

    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return (round(float(value)), 0)
    return None


def parse_quantity(text: str) -> tuple[float, str] | None:
    found = _QUANTITY.search(text or "")
    if not found:
        return None
    sign = -1.0 if found.group(1) == "-" else 1.0
    return (sign * float(found.group(2)), unit_kind(found.group(3)))


def unit_kind(raw: str) -> str:
    # Whitespace is not part of a unit ("° C" is °C), but the case of an SI
    # prefix is: mΩ and MΩ are a thousand million apart.
    unit = re.sub(r"\s+", "", (raw or "").strip())
    lower = unit.lower()
    if lower.startswith("%"):
        return "percent"
    if lower.startswith("°") or lower.startswith("deg"):
        if lower.endswith("c"):
            return "°C"
        if lower.endswith("f"):
            return "°F"
        if lower.endswith("k"):
            return "K"
    if lower in ("k", "°k", "degk", "degreek", "degreesk"):
        return "K"

    ohms = re.fullmatch(r"([kKmM]?)(?:ω|ohms?)", unit, re.I)
    if ohms:
        prefix = ohms.group(1)
        return {"": "Ohm", "m": "mOhm", "M": "MOhm", "k": "kOhm", "K": "kOhm"}.get(
            prefix, f"{prefix}Ohm"
        )

    if lower == "mm/s":
        return "mm/s"
    return {
        "mm": "mm", "bar": "bar", "mbar": "mbar", "pa": "Pa", "hpa": "hPa",
        "kpa": "kPa", "mpa": "MPa", "psi": "psi", "psig": "psig", "psia": "psia",
        "ma": "mA", "mv": "mV", "v": "V", "hz": "Hz", "rpm": "rpm",
    }.get(lower, unit)


def add_offset(start: date, months: int = 0, days: int = 0) -> date:
    year = start.year + (start.month - 1 + months) // 12
    month = (start.month - 1 + months) % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(days=days)


def _iso(value: date | None) -> str:
    return value.isoformat() if value else "-"


def _quantity_text(quantity: tuple[float, str]) -> str:
    value, kind = quantity
    sign = "+" if value > 0 else ""
    return f"{sign}{value:g} {kind}"


def _headline(
    rows: list[Assessment],
    out_of_tolerance: list[Assessment],
    overdue: list[Assessment],
    missing: list[Assessment],
    unproven: list[Assessment],
    cal_after_reading: list[Assessment],
    unreadable_dates: list[Assessment],
    skipped: int,
    due_soon: list[Assessment],
) -> str:
    parts = []
    if out_of_tolerance:
        parts.append(
            f"{len(out_of_tolerance)} instrument{'s' if len(out_of_tolerance) != 1 else ''} out of tolerance"
        )
    if overdue:
        parts.append(f"{len(overdue)} out of calibration")
    if missing:
        parts.append(f"{len(missing)} with no calibration date")
    if unproven:
        parts.append(f"{len(unproven)} with an as-found result that cannot be checked")
    if cal_after_reading:
        parts.append(f"{len(cal_after_reading)} calibrated after the reading date")
    if unreadable_dates:
        parts.append(f"{len(unreadable_dates)} with an unreadable date")
    if skipped:
        parts.append(f"{skipped} register row{'s' if skipped != 1 else ''} skipped")
    if due_soon:
        parts.append(f"{len(due_soon)} due for recalibration")
    if not parts:
        return f"No calibration problems for the {len(rows)} instrument{'s' if len(rows) != 1 else ''} assessed."
    return "**Attention required:** " + "; ".join(parts) + "."


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
