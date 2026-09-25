"""
title: 4CE Engineering Calculations
author: 4CE
version: 0.1.0
description: Deterministic engineering calculations with every step shown and units carried - thickness-based corrosion rate, remaining life and the next inspection interval. Arithmetic done on this machine, not by a model.
"""

import json
import re
from typing import Awaitable, Callable

from pydantic import BaseModel, Field

# Small counts people write as words: "three years ago".
_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
}
_NUM = r"(\d+(?:\.\d+)?)"
_YEARS = r"(\d+(?:\.\d+)?|" + "|".join(_WORDS) + r")\s*(?:years?|yrs?)"

# Each quantity as it is commonly written in an inspection report or a
# request. First pattern that matches wins, so the specific come first.
_PATTERNS = {
    "previous": [
        rf"(?:previous|prior|earlier|original|initial|last|baseline)\s+(?:wall\s+)?thickness[^0-9\n]{{0,30}}{_NUM}\s*mm",
        rf"{_NUM}\s*mm\s+(?:\w+\s+){{0,3}}(?:previously|before|originally|at the last inspection)",
    ],
    "current": [
        rf"(?:current|present|measured|actual|latest|now|minimum measured)\s+(?:wall\s+)?thickness[^0-9\n]{{0,30}}{_NUM}\s*mm",
        rf"(?:now|today|currently)\s+(?:\w+\s+){{0,2}}{_NUM}\s*mm",
    ],
    "required": [
        rf"(?:required|retirement|minimum required|minimum allowable|min(?:imum)?\.?\s+required|t[_\s-]?req(?:uired)?)\s*(?:wall\s+)?(?:thickness)?[^0-9\n]{{0,30}}{_NUM}\s*mm",
    ],
    "years": [
        rf"{_YEARS}\s+(?:ago|apart|earlier|before|between|of service|in service)",
        rf"(?:over|after|interval of|in the last|across|within)\s+{_YEARS}",
    ],
    "max_interval": [
        rf"(?:maximum|max\.?|code)\s+(?:inspection\s+)?interval[^0-9\n]{{0,25}}{_YEARS}",
    ],
}

# A thickness survey as a table: which header means which quantity. An
# interval a rule requires for one location is a column of its own, matched
# before the readings' own interval so "SOP interval" is not taken for Δt.
_COLUMNS = {
    "max_interval": ("sop interval", "max interval", "maximum interval"),
    "previous": ("previous", "prev", "prior", "original", "initial", "baseline", "last"),
    "current": ("current", "measured", "actual", "latest", "present"),
    "required": ("required", "retirement", "t_req", "treq", "minimum allowable", "min required"),
    "years": ("years", "interval", "yrs", "Δt", "delta t"),
}


class Tools:
    class Valves(BaseModel):
        default_max_interval_years: float = Field(
            default=0.0,
            description="The code's maximum inspection interval, in years, used when a request does not give one. 0 leaves it unstated.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def calculate_remaining_life(
        self,
        readings: str,
        max_interval_years: float = 0.0,
        interval_basis: str = "",
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Calculate corrosion rate, remaining life and the next inspection interval from wall-thickness readings, showing every step with units.

        Use this whenever a request gives wall thicknesses to assess - a previous and a current
        thickness, the required or retirement thickness, and the time between the readings -
        whether in a sentence or as a thickness-survey table. The arithmetic is done here, not by
        a model, and each step is returned so it can be quoted and checked.

        :param readings: The readings, as written: a sentence such as "12.0 mm three years ago, 11.2 mm now, required 9.5 mm", or a markdown table with previous, current and required thickness columns.
        :param max_interval_years: A maximum interval between measurements that applies here, in years - from a code, or a plant SOP. 0 when there is none.
        :param interval_basis: What sets that maximum, e.g. "the interval SOP-MEC-014 §4.2 requires".
        :return: The worked calculation in markdown, followed by a machine-readable block of the inputs.
        """
        await _emit(__event_emitter__, "calculation", "Calculating remaining life from the thickness readings")
        rows, interval = _parse(readings or "")
        basis = "the code maximum"
        if interval is None and self.valves.default_max_interval_years > 0:
            interval = self.valves.default_max_interval_years
        # A shorter interval a plant rule requires governs the next measurement:
        # the arithmetic says when corrosion would matter, the SOP says when to look.
        if max_interval_years and max_interval_years > 0 and (interval is None or max_interval_years < interval):
            interval, basis = float(max_interval_years), interval_basis or "the stated maximum"
        if not rows:
            await _emit(__event_emitter__, "calculation", "Not enough readings to calculate", done=True)
            return (
                "Remaining life could not be calculated: it needs a previous and a current wall "
                "thickness, the required (retirement) thickness, all in mm, and the years between "
                "the two readings."
            )
        # A location with an interval of its own - the SOP's six months where
        # its wall margin is thin - takes the shorter of that and the rest's.
        results = []
        for row in rows:
            own = row.pop("max_interval", None)
            if own and own > 0 and (interval is None or own < interval):
                results.append(dict(_remaining_life(row, own), basis=interval_basis or "the interval set for it"))
            else:
                results.append(dict(_remaining_life(row, interval), basis=basis))
        await _emit(
            __event_emitter__, "calculation",
            f"Remaining life calculated for {len(results)} location{'' if len(results) == 1 else 's'}",
            done=True,
        )
        return _report(results, interval, basis)


def _number(text: str) -> float:
    return float(_WORDS.get(text.lower(), text))


def _find(key: str, text: str) -> float | None:
    for pattern in _PATTERNS[key]:
        found = re.search(pattern, text, re.I)
        if found:
            return _number(found.group(1))
    return None


def _parse(text: str) -> tuple[list[dict], float | None]:
    interval = _find("max_interval", text)
    rows = _parse_table(text)
    if not rows:
        row = {k: _find(k, text) for k in ("previous", "current", "required", "years")}
        if all(row[k] is not None for k in ("previous", "current", "required", "years")):
            row["location"] = ""
            rows = [row]
    else:
        # A table without a years column takes the interval the text states.
        years = _find("years", text)
        rows = [r for r in rows if r.get("years") is not None or years is not None]
        for r in rows:
            if r.get("years") is None:
                r["years"] = years
    return rows, interval


def _parse_table(text: str) -> list[dict]:
    lines = [l.strip() for l in text.splitlines()]
    for i in range(len(lines) - 1):
        if not (lines[i].startswith("|") and re.match(r"^\|?\s*:?-{2,}", lines[i + 1])):
            continue
        header = [c.strip().lower() for c in lines[i].strip("|").split("|")]
        columns: dict[str, int] = {}
        for key, words in _COLUMNS.items():
            for n, name in enumerate(header):
                if n not in columns.values() and any(w in name for w in words):
                    columns[key] = n
                    break
        if not all(k in columns for k in ("previous", "current", "required")):
            continue
        rows = []
        for line in lines[i + 2:]:
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip("|").split("|")]
            values = {}
            for key, n in columns.items():
                found = re.search(_NUM, cells[n]) if n < len(cells) else None
                values[key] = float(found.group(1)) if found else None
            if values.get("max_interval") is None:
                values.pop("max_interval", None)
            if all(values.get(k) is not None for k in ("previous", "current", "required")):
                label = next((c for n, c in enumerate(cells) if n not in columns.values() and c), "")
                rows.append({"location": re.sub(r"[*_`]", "", label), **values})
        if rows:
            return rows
    return []


def _remaining_life(row: dict, max_interval: float | None) -> dict:
    prev, cur, req, years = row["previous"], row["current"], row["required"], row["years"]
    result = dict(row, max_interval=max_interval)
    loss = prev - cur
    rate = loss / years if years else None
    result["rate"] = rate
    if cur <= req:
        result.update(life=0.0, next=0.0, verdict="AT OR BELOW REQUIRED THICKNESS")
    elif rate is None or rate <= 0:
        result.update(life=None, next=max_interval, verdict="NO MEASURABLE WALL LOSS")
    else:
        life = (cur - req) / rate
        half = life / 2
        result.update(
            life=life,
            next=min(half, max_interval) if max_interval else half,
            verdict="FIT FOR CONTINUED SERVICE",
        )
    return result


def _mm(value: float) -> str:
    return f"{value:.1f} mm" if abs(value * 10 - round(value * 10)) < 1e-9 else f"{value:.2f} mm"


def _yr(value: float, places: int = 1) -> str:
    return f"{value:.{places}f} year{'' if abs(value - 1) < 1e-9 else 's'}"


def _when(years: float) -> str:
    """An interval as a person would say it: months under a year."""
    if years < 1:
        months = round(years * 12)
        return f"{months} month{'' if months == 1 else 's'}"
    return _yr(years)


def _steps(r: dict) -> list[str]:
    lines = [
        f"**Inputs.** Previous thickness t_prev = {_mm(r['previous'])} · current thickness "
        f"t_act = {_mm(r['current'])} · required thickness t_req = {_mm(r['required'])} · "
        f"interval Δt = {_yr(r['years'], 0 if float(r['years']).is_integer() else 1)}",
    ]
    if r["rate"] is None:
        return lines + ["The interval between readings is zero, so no rate can be calculated."]
    lines.append(
        f"**Step 1 - corrosion rate.** CR = (t_prev - t_act) ÷ Δt = ({_mm(r['previous'])} - "
        f"{_mm(r['current'])}) ÷ {_yr(r['years'], 0 if float(r['years']).is_integer() else 1)} "
        f"= **{r['rate']:.3f} mm/year**"
    )
    if r["verdict"] == "AT OR BELOW REQUIRED THICKNESS":
        lines.append(
            f"**Step 2 - remaining life.** t_act {_mm(r['current'])} is at or below t_req "
            f"{_mm(r['required'])}: **no remaining life**."
        )
        lines.append("**Result.** At or below the required thickness: remove from service or "
                     "assess fitness for service before further operation.")
        return lines
    if r["verdict"] == "NO MEASURABLE WALL LOSS":
        lines.append(
            "**Step 2 - remaining life.** The rate is zero or negative - no measurable wall loss "
            "over the interval - so remaining life is not limited by corrosion on this data."
        )
        lines.append("**Result.** Fit for continued service; re-measure at the code's normal interval.")
        return lines
    lines.append(
        f"**Step 2 - remaining life.** RL = (t_act - t_req) ÷ CR = ({_mm(r['current'])} - "
        f"{_mm(r['required'])}) ÷ {r['rate']:.3f} mm/year = **{_yr(r['life'])}**"
    )
    half = r["life"] / 2
    if r["max_interval"]:
        lines.append(
            f"**Step 3 - next thickness measurement.** The lesser of RL ÷ 2 ({_yr(half)}) and "
            f"{r.get('basis', 'the code maximum')} ({_when(r['max_interval'])}) = **{_when(r['next'])}**"
        )
    else:
        lines.append(
            f"**Step 3 - next thickness measurement.** Within RL ÷ 2 = **{_yr(half)}**, and not later "
            "than the code's maximum interval for this piping class (not supplied)."
        )
    lines.append(
        f"**Result.** Fit for continued service; measure the thickness again within "
        f"{_when(r['next'])}" + ("" if r["max_interval"] else ", subject to the code maximum") + "."
    )
    return lines


def _report(results: list[dict], interval: float | None, basis: str = "the code maximum") -> str:
    out = [
        "## Remaining life - thickness method",
        "",
        "*Deterministic arithmetic on this machine: every step shown, units carried. The method "
        "is the thickness-based one common in piping inspection codes such as API 570.*",
        "",
    ]
    if len(results) > 1:
        out += [
            "| Location | t_prev (mm) | t_act (mm) | t_req (mm) | Δt (years) | CR (mm/year) | RL (years) | Next measurement (years) | Verdict |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in results:
            rate = "-" if r["rate"] is None else f"{r['rate']:.3f}"
            life = "-" if r["life"] is None else f"{r['life']:.1f}"
            due = "-" if r["next"] is None else f"{r['next']:.1f}"
            out.append(
                f"| {r['location'] or '-'} | {r['previous']:g} | {r['current']:g} | {r['required']:g} | "
                f"{r['years']:g} | {rate} | {life} | {due} | {r['verdict']} |"
            )
        governing = min(results, key=lambda r: float("inf") if r["life"] is None else r["life"])
        out += ["", f"### Governing location: {governing['location'] or 'as given'}", ""]
        out += _steps(governing)
    else:
        out += _steps(results[0])
    data = {
        "kind": "remaining_life",
        "max_interval": interval,
        "basis": basis if interval else "",
        "rows": [
            {k: r[k] for k in ("location", "previous", "current", "required", "years")}
            | ({"max_interval": r["max_interval"]} if r.get("max_interval") != interval else {})
            for r in results
        ],
    }
    return "\n\n".join(out).replace("\n\n|", "\n|") + "\n\n```4ce-calc\n" + json.dumps(data) + "\n```"


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
