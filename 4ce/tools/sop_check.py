"""
title: 4CE SOP Threshold Check
author: 4CE
version: 0.1.0
description: Assesses inspection readings against the thresholds written in a standard operating procedure and returns a clause-cited fit-for-service verdict. Every comparison is arithmetic performed locally, not a judgement made by a model.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

# Ordered least to most restrictive. The overall disposition is the worst one
# any single rule returned.
DISPOSITIONS = [
    "FIT FOR SERVICE",
    "FIT FOR SERVICE WITH CONDITIONS",
    "NOT FIT FOR START",
    "REMOVE FROM SERVICE",
]

# Lines that look like a measurement but matched no rule are reported as
# unassessed rather than quietly ignored. Longest unit alternatives first, or
# "mm/s" would be swallowed by "mm".
MEASUREMENT = re.compile(
    r"\d+(?:\.\d+)?\s*(?:mm/s|degrees?\s*C|deg\s*C|°\s*C|bar|mm|kPa|psi|rpm|Hz|%|drops?)\b",
    re.IGNORECASE,
)

DEFAULT_RULE_PACK: dict[str, Any] = {
    "sop_id": "SOP-MEC-014",
    "title": "Mechanical Seal Leakage - Assessment and Action",
    "rules": [
        {
            "id": "seal_leakage",
            "parameter": "Seal leakage",
            "unit": "drops/min",
            "type": "band",
            "limit": "below 5 drops/min",
            "patterns": [
                r"(\d+(?:\.\d+)?)\s*(?:to|-|–|—)\s*(\d+(?:\.\d+)?)\s*drops?\s*(?:per|/)\s*min",
                r"(\d+(?:\.\d+)?)\s*drops?\s*(?:per|/)\s*min",
            ],
            "bands": [
                {
                    "below": 5,
                    "verdict": "PASS",
                    "clause": "2.1",
                    "disposition": "FIT FOR SERVICE",
                },
                {
                    "max": 20,
                    "verdict": "REVIEW",
                    "clause": "2.2",
                    "action": "Continued operation requires the area supervisor's written concurrence. Schedule seal replacement within 30 days.",
                    "disposition": "FIT FOR SERVICE WITH CONDITIONS",
                },
                {
                    "verdict": "FAIL",
                    "clause": "2.3",
                    "action": "Seal leakage is above 20 drops per minute. Remove the equipment from service immediately.",
                    "disposition": "REMOVE FROM SERVICE",
                },
            ],
        },
        {
            "id": "seal_spray",
            "parameter": "Seal atomisation / spray",
            "type": "presence",
            "limit": "no atomised or visible spray",
            "defect_patterns": [
                r"atomis(?:ed|ing|ation)",
                r"atomiz(?:ed|ing|ation)",
                r"visible spray",
                r"spray(?:ing)?\s+from\s+the\s+seal",
            ],
            "defect": {
                "verdict": "FAIL",
                "clause": "2.3",
                "action": "Atomised or visible spray observed. Remove the equipment from service immediately.",
                "disposition": "REMOVE FROM SERVICE",
            },
            "clear": {"verdict": "PASS", "clause": "2.3", "disposition": "FIT FOR SERVICE"},
        },
        {
            "id": "vibration",
            "parameter": "Vibration (ISO 10816)",
            "type": "categorical",
            "limit": "Zone A or B",
            "patterns": [r"zone\s*([A-D])\b"],
            # A velocity is not a zone: the ISO 10816 boundaries depend on the
            # machine's class, which this SOP does not give. Recognised, so the
            # report says what was supplied, and deliberately not converted.
            "unconverted": {
                "patterns": [r"(\d+(?:\.\d+)?)\s*mm\s*/\s*s"],
                "note": "{value} mm/s was given, but this SOP states vibration as ISO 10816 zones, "
                        "whose boundaries depend on the machine class - state the zone to have it assessed",
            },
            "cases": {
                "A": {"verdict": "PASS", "clause": "3.1", "disposition": "FIT FOR SERVICE"},
                "B": {"verdict": "PASS", "clause": "3.1", "disposition": "FIT FOR SERVICE"},
                "C": {
                    "verdict": "REVIEW",
                    "clause": "3.2",
                    "action": "Zone C permits operation for a limited period only. Raise a maintenance notification.",
                    "disposition": "FIT FOR SERVICE WITH CONDITIONS",
                },
                "D": {
                    "verdict": "FAIL",
                    "clause": "3.3",
                    "action": "Zone D is not acceptable. Remove the equipment from service.",
                    "disposition": "REMOVE FROM SERVICE",
                },
            },
        },
        {
            "id": "wall_thickness",
            "parameter": "Wall thickness",
            "unit": "mm",
            "type": "margin",
            "limit": "above the retirement thickness",
            "patterns": [
                r"minimum measured wall thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
                r"measured wall thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
                # How a thickness survey or a remaining-life request says it: the
                # latest reading is the measured thickness §4.1 is about. Missed,
                # a 1.7 mm margin went unassessed and §4.2's six-month interval
                # with it, while the answer scheduled the next check in 3.2 years.
                r"(?:current|present|actual|latest)\s+(?:wall\s+)?thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
                r"(?<!previous )(?<!prior )(?<!original )wall thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
            ],
            "reference_patterns": [
                r"retirement thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
                r"(?:required|minimum required|minimum allowable)\s+(?:wall\s+)?thickness[^0-9]{0,40}(\d+(?:\.\d+)?)\s*mm",
            ],
            "pass": {"verdict": "PASS", "clause": "4.1", "disposition": "FIT FOR SERVICE"},
            "fail": {
                "verdict": "FAIL",
                "clause": "4.1",
                "action": "Minimum measured wall thickness is at or below the retirement thickness. Remove the equipment from service.",
                "disposition": "REMOVE FROM SERVICE",
            },
            "secondary": {
                "margin_below": 2.0,
                "clause": "4.2",
                "action": "Remaining wall thickness margin is below 2.0 mm. Shorten the inspection interval to six months.",
            },
        },
        {
            "id": "coupling_guard",
            "parameter": "Coupling guard",
            "type": "presence",
            "limit": "no coupling guard fastener missing",
            # A shift log says "bolt" where an inspection form says "fastener".
            "defect_patterns": [
                r"(?:coupling\s+)?guard[^.\n]{0,60}(?:fastener|bolt|screw|nut|fixing)s?[^.\n]{0,40}missing[^.\n]{0,30}",
                r"missing[^.\n]{0,30}(?:coupling\s+)?guard\s+(?:fastener|bolt|screw|nut|fixing)s?",
            ],
            "defect": {
                "verdict": "FAIL",
                "clause": "5.1",
                "action": "Rectify the missing coupling guard fastener before the next start.",
                "disposition": "NOT FIT FOR START",
            },
            "clear": {"verdict": "PASS", "clause": "5.1", "disposition": "FIT FOR SERVICE"},
        },
    ],
}


@dataclass
class Finding:
    parameter: str
    measured: str
    limit: str
    clause: str
    verdict: str
    disposition: str = "FIT FOR SERVICE"
    actions: list[tuple[str, str]] = field(default_factory=list)


class Tools:
    class Valves(BaseModel):
        rule_pack: str = Field(
            default="",
            description="JSON rule pack defining the SOP thresholds to assess against. Leave blank to use the built-in SOP-MEC-014 pack.",
        )
        block_on_missing_data: bool = Field(
            default=True,
            description="Treat a rule with no matching reading as blocking, so an incomplete assessment can never read as fit for service.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False

    async def check_sop_thresholds(
        self,
        readings: str,
        __event_emitter__: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """
        Assess inspection readings against SOP thresholds and return a clause-cited fit-for-service verdict.

        Use this whenever a measured value has to be compared against a limit, tolerance or
        acceptance criterion - seal leakage rates, vibration zones, wall thickness against a
        retirement thickness, missing guarding. Do not perform the comparison yourself: pass the
        readings here and report what comes back, because this tool does the arithmetic locally
        and cites the SOP clause that decided each one.

        :param readings: The observations and measurements to assess. Either the relevant text of
            the inspection report, or a short 'parameter: value' list extracted from it. Include
            units, and include both the measured and retirement thickness where wall loss applies.
        :return: A table of every assessed parameter with its measured value, the applicable limit,
            the SOP clause and the verdict, followed by the required actions and an overall disposition.
        """
        await _emit(__event_emitter__, "sop_check", "Assessing readings against SOP thresholds")

        text = (readings or "").strip()
        if not text:
            await _emit(__event_emitter__, "sop_check", "No readings supplied", done=True)
            return (
                "No readings were supplied, so nothing was assessed. Pass the measurements from "
                "the inspection report - including units - and the assessment will run against "
                "the SOP thresholds."
            )

        try:
            pack = self._rule_pack()
        except ValueError as exc:
            await _emit(__event_emitter__, "sop_check", "Rule pack is invalid", done=True)
            return (
                f"The SOP rule pack could not be read: {exc}\n\n"
                "No assessment was performed. Fix the `rule_pack` valve, or clear it to fall back "
                "to the built-in SOP-MEC-014 pack. It is not safe to guess at thresholds."
            )

        sop_id = str(pack.get("sop_id") or "SOP")
        rules = pack.get("rules") or []

        findings: list[Finding] = []
        matched_spans: list[tuple[int, int]] = []
        for rule in rules:
            finding, spans = _assess(rule, text)
            findings.append(finding)
            matched_spans.extend(spans)

        unassessed = _unassessed_lines(text, matched_spans)

        assessed = [f for f in findings if f.verdict != "NO DATA"]
        failures = [f for f in findings if f.verdict == "FAIL"]
        reviews = [f for f in findings if f.verdict == "REVIEW"]
        missing = [f for f in findings if f.verdict == "NO DATA"]
        incomplete = bool(missing) and self.valves.block_on_missing_data

        disposition = _worst(f.disposition for f in findings)
        if incomplete and not failures:
            disposition = "ASSESSMENT INCOMPLETE"

        clear = not failures and not reviews and not incomplete
        await _emit(
            __event_emitter__,
            "sop_check",
            f"{sop_id}: {len(assessed) - len(failures) - len(reviews)}/{len(assessed)} parameters within limits",
            done=True,
        )

        lines = [
            f"## SOP assessment - {sop_id} - {'PASS' if clear else 'ATTENTION REQUIRED'}",
            "",
            _headline(assessed, failures, reviews, missing),
            "",
            "| Parameter | Measured | Acceptance limit | Clause | Verdict |",
            "|---|---|---|---|---|",
        ]
        for finding in findings:
            clause = f"§{finding.clause}" if finding.clause else "-"
            lines.append(
                f"| {finding.parameter} | {finding.measured} | {finding.limit} | {clause} | {finding.verdict} |"
            )

        required = [action for finding in findings for action in finding.actions]
        if required:
            lines += ["", "### Required actions", ""]
            for clause, action in required:
                lines.append(f"- **§{clause}** - {action}")

        if missing:
            lines += ["", "### Not measured", ""]
            for finding in missing:
                detail = finding.measured[len("not found ("):-1] if finding.measured.startswith("not found (") else ""
                lines.append(
                    f"- **{finding.parameter}** - "
                    + (f"{detail}. " if detail else "no reading found in the material supplied. ")
                    + f"{sop_id} §{finding.clause} could not be applied."
                )

        if unassessed:
            lines += ["", "### Readings outside this SOP", ""]
            for line in unassessed:
                lines.append(f"- {line}")
            lines.append(
                f"\nThese carry a measurement but match no rule in {sop_id}. They were **not** "
                "assessed. Check them against the SOP that governs them."
            )

        lines += ["", f"**Disposition: {disposition}**"]
        if incomplete and not failures:
            lines.append(
                "\n> One or more thresholds could not be applied because the reading was absent. "
                "The assessment is treated as blocking rather than passing: supply the missing "
                "measurements and re-run before releasing the equipment."
            )

        lines.append(
            f"\n*Assessed against {sop_id} only, and only for the parameters in its rule pack. "
            "Every comparison above is arithmetic performed on this machine against an authored "
            "threshold - no model judged whether a value was acceptable. Defect checks such as "
            "guarding infer from what the report states; a defect that was never inspected for "
            "cannot be detected here.*"
        )
        return "\n".join(lines)

    def _rule_pack(self) -> dict[str, Any]:
        raw = (self.valves.rule_pack or "").strip()
        if not raw:
            return DEFAULT_RULE_PACK
        try:
            pack = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno} ({exc.msg})") from exc
        if not isinstance(pack, dict) or not isinstance(pack.get("rules"), list):
            raise ValueError("expected an object with a 'rules' list")
        return pack


def _assess(rule: dict[str, Any], text: str) -> tuple[Finding, list[tuple[int, int]]]:
    kind = rule.get("type")
    if kind == "band":
        return _assess_band(rule, text)
    if kind == "categorical":
        return _assess_categorical(rule, text)
    if kind == "margin":
        return _assess_margin(rule, text)
    if kind == "presence":
        return _assess_presence(rule, text)
    return _no_data(rule, f"unsupported rule type '{kind}'"), []


def _assess_band(rule: dict[str, Any], text: str) -> tuple[Finding, list[tuple[int, int]]]:
    match = _first_match(rule.get("patterns", []), text)
    if not match:
        return _no_data(rule), []

    values = [float(g) for g in match.groups() if g is not None]
    # A reported range is assessed at its worse end: conservatism is the right
    # default for an integrity decision.
    value = max(values)
    unit = rule.get("unit", "")
    measured = (" to ".join(_fmt(v) for v in values) + f" {unit}").strip()

    for band in rule.get("bands", []):
        if not _in_band(value, band):
            continue
        return _finding(rule, measured, band, rule.get("limit", "")), [match.span()]
    return _no_data(rule, "no band matched"), [match.span()]


def _assess_categorical(rule: dict[str, Any], text: str) -> tuple[Finding, list[tuple[int, int]]]:
    match = _first_match(rule.get("patterns", []), text)
    if not match or not match.groups():
        return _no_data(rule, _unconverted(rule, text)), []

    key = match.group(1).strip().upper()
    case = (rule.get("cases") or {}).get(key)
    if case is None:
        return _no_data(rule, f"'{key}' is not a recognised class"), [match.span()]
    return _finding(rule, match.group(0).strip(), case, rule.get("limit", "")), [match.span()]


def _assess_margin(rule: dict[str, Any], text: str) -> tuple[Finding, list[tuple[int, int]]]:
    measured_match = _first_match(rule.get("patterns", []), text)
    reference_match = _first_match(rule.get("reference_patterns", []), text)
    if not measured_match or not reference_match:
        return _no_data(rule, "measured and retirement thickness are both required"), []

    measured_value = float(measured_match.group(1))
    reference_value = float(reference_match.group(1))
    margin = measured_value - reference_value
    unit = rule.get("unit", "")
    spans = [measured_match.span(), reference_match.span()]

    outcome = rule["pass"] if margin > 0 else rule["fail"]
    display = f"{_fmt(measured_value)} {unit} ({_fmt(margin)} {unit} margin)".strip()
    limit = f"above {_fmt(reference_value)} {unit} retirement".strip()
    finding = _finding(rule, display, outcome, limit)

    secondary = rule.get("secondary") or {}
    threshold = secondary.get("margin_below")
    if threshold is not None and margin > 0 and margin < float(threshold):
        finding.actions.append((str(secondary.get("clause", "")), str(secondary.get("action", ""))))

    return finding, spans


# "No visible spray" and "guard fasteners: none missing" report the defect
# absent. Matched as they stood, both failed the equipment - the first with
# REMOVE FROM SERVICE.
_DENIED_BEFORE = re.compile(r"\b(?:no|not|nil|without)\s+(?:\w+\s+){0,2}$", re.IGNORECASE)
_DENIED_WITHIN = re.compile(r"\b(?:none|nothing|not|no)\s+missing\b", re.IGNORECASE)


def _assess_presence(rule: dict[str, Any], text: str) -> tuple[Finding, list[tuple[int, int]]]:
    for pattern in rule.get("defect_patterns", []):
        for match in re.finditer(pattern, text, re.IGNORECASE):
            before = text[max(0, match.start() - 30):match.start()]
            if _DENIED_BEFORE.search(before) or _DENIED_WITHIN.search(match.group(0)):
                continue
            return _finding(rule, match.group(0).strip(), rule["defect"], rule.get("limit", "")), [match.span()]
    return _finding(rule, "not reported", rule["clear"], rule.get("limit", "")), []


def _finding(rule: dict[str, Any], measured: str, outcome: dict[str, Any], limit: str) -> Finding:
    finding = Finding(
        parameter=str(rule.get("parameter", rule.get("id", "-"))),
        measured=measured or "-",
        limit=limit or rule.get("limit", "") or "-",
        clause=str(outcome.get("clause", "")),
        verdict=str(outcome.get("verdict", "NO DATA")),
        disposition=str(outcome.get("disposition", "FIT FOR SERVICE")),
    )
    action = outcome.get("action")
    if action and finding.verdict != "PASS":
        finding.actions.append((finding.clause, str(action)))
    return finding


def _unconverted(rule: dict[str, Any], text: str) -> str:
    """What was supplied instead of the reading a rule needs, when it says so."""
    spec = rule.get("unconverted") or {}
    found = _first_match(spec.get("patterns", []), text)
    if not found or not spec.get("note"):
        return ""
    return str(spec["note"]).format(value=found.group(1))


def _no_data(rule: dict[str, Any], detail: str = "") -> Finding:
    return Finding(
        parameter=str(rule.get("parameter", rule.get("id", "-"))),
        measured=f"not found ({detail})" if detail else "not found",
        limit=str(rule.get("limit", "") or "-"),
        clause=str(rule.get("clause", "") or _first_clause(rule)),
        verdict="NO DATA",
        disposition="FIT FOR SERVICE",
    )


def _first_clause(rule: dict[str, Any]) -> str:
    for key in ("bands", "cases"):
        block = rule.get(key)
        entries = block if isinstance(block, list) else list((block or {}).values())
        for entry in entries:
            if isinstance(entry, dict) and entry.get("clause"):
                return str(entry["clause"])
    for key in ("pass", "defect", "clear"):
        entry = rule.get(key)
        if isinstance(entry, dict) and entry.get("clause"):
            return str(entry["clause"])
    return ""


def _in_band(value: float, band: dict[str, Any]) -> bool:
    if "below" in band:
        return value < float(band["below"])
    if "max" in band:
        return value <= float(band["max"])
    return True


def _first_match(patterns: list[str], text: str) -> re.Match | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def _unassessed_lines(text: str, spans: list[tuple[int, int]]) -> list[str]:
    lines, offset = [], 0
    for raw in text.splitlines(keepends=True):
        start, end = offset, offset + len(raw)
        offset = end
        stripped = raw.strip()
        if not stripped or not MEASUREMENT.search(stripped):
            continue
        if any(s < end and e > start for s, e in spans):
            continue
        lines.append(stripped if len(stripped) <= 120 else stripped[:117] + "...")
    return lines


def _worst(dispositions) -> str:
    return max(
        (d for d in dispositions if d in DISPOSITIONS),
        key=DISPOSITIONS.index,
        default="FIT FOR SERVICE",
    )


def _headline(assessed: list[Finding], failures: list[Finding], reviews: list[Finding], missing: list[Finding]) -> str:
    within = len(assessed) - len(failures) - len(reviews)
    parts = [f"**{within} of {len(assessed)} assessed parameters within limits.**"]
    if failures:
        parts.append(f"{len(failures)} outside limits.")
    if reviews:
        parts.append(f"{len(reviews)} requires review.")
    if missing:
        parts.append(f"{len(missing)} could not be assessed.")
    return " ".join(parts)


def _fmt(value: float) -> str:
    return f"{value:g}"


async def _emit(emitter, action: str, description: str, done: bool = False) -> None:
    if emitter:
        await emitter({"type": "status", "data": {"action": action, "description": description, "done": done}})
