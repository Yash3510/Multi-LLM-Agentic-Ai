# SOP Threshold Checker — plan

`tools/sop_check.py` — a fourth 4CE tool. It takes the readings observed in an
inspection report and decides, against the thresholds written in an SOP, whether
the equipment is fit for service — returning a clause-cited table rather than an
opinion.

## Why this tool exists

Today the chain can read a report and *say* the seal is weeping at 3–4 drops per
minute. Whether that is acceptable depends on SOP-MEC-014 §2.1, and right now
nothing but the model's own judgement connects the two. A language model doing
threshold arithmetic is the weakest link in the demo: it is exactly the step
that looks right and is occasionally wrong, and ULTRON grading it is one model
checking another's mental maths.

So the tool is the **deterministic arbiter**. The model extracts readings; the
tool applies the rules with real comparisons and cites the clause it applied.
That turns "the assistant read the document" into "the assistant caught a
guard fastener missing, cited §5.1, and withheld return-to-service" — which is
the difference between a demo that reads well and one that holds up under
questioning.

## Design stance

**Rules are data, the engine is generic.** The comparison logic knows nothing
about pumps. It evaluates a rule pack: a JSON list where each rule names a
parameter, a clause reference, a comparison, and the action that follows. The
pack ships with SOP-MEC-014 encoded, and is editable in a Valve so a different
SOP can be loaded without touching code.

**Arithmetic never reaches the model.** Every numeric comparison, band lookup
and margin calculation happens in Python. The model's only job is to hand over
the readings it found.

**Fails closed.** A measurement rule with no matching reading reports `NO DATA`,
not `PASS`, and the disposition becomes `ASSESSMENT INCOMPLETE` — mirroring the
approval gate, which already treats silence as refusal rather than consent.
Readings that carry a measurement but match no rule are listed separately as
outside the SOP, so a clean table can never be mistaken for full coverage.

The one deliberate exception is **defect-presence rules** (spray, missing
guarding). These assess whether a defect was *reported*, and inspectors report
defects; absence of the phrase is recorded as `not reported` and passes. Making
these `NO DATA` would mark every report incomplete for defects nobody found,
which trains the reader to ignore the incomplete flag — worse for safety than
the narrower claim. The footer states this limitation outright.

**Cites, always.** Every row carries the clause (`SOP-MEC-014 §2.2`) that
decided it. This is what makes the output auditable and what the citation guard
will later be able to check.

## Rule pack schema

```json
{
  "sop_id": "SOP-MEC-014",
  "title": "Mechanical Seal Leakage — Assessment and Action",
  "rules": [
    {
      "id": "seal_leakage",
      "parameter": "Seal leakage",
      "clause": "2",
      "unit": "drops/min",
      "type": "band",
      "patterns": ["(\\d+(?:\\.\\d+)?)\\s*(?:to|-|–)\\s*(\\d+(?:\\.\\d+)?)\\s*drops?\\s*per\\s*minute"],
      "bands": [
        {"max": 5,  "verdict": "PASS",   "clause": "2.1", "action": "Acceptable. Record and monitor at the next routine round."},
        {"max": 20, "verdict": "REVIEW", "clause": "2.2", "action": "Supervisor's written concurrence required. Schedule seal replacement within 30 days."},
        {"max": null, "verdict": "FAIL", "clause": "2.3", "action": "Remove from service immediately."}
      ]
    }
  ]
}
```

Rule `type` values to support:

| Type | Use | Example |
|---|---|---|
| `band` | Ordered numeric ranges, each with its own verdict and action | Seal leakage §2 |
| `categorical` | A named class maps to a verdict | ISO 10816 Zone A/B/C/D §3 |
| `margin` | Two readings compared, verdict on the difference | Wall thickness vs. retirement thickness §4 |
| `presence` | A defect phrase either appears or does not | Missing guard fastener §5.1 |

Where a reading is a range (`3 to 4 drops per minute`), the **worst** end is
assessed. Conservatism is the right default for an integrity decision.

## Extraction

Two sources, in order of preference:

1. **Caller-supplied readings** — the model passes `readings` as a short
   `parameter: value` block it extracted. Preferred, since the model has already
   done the OCR/vision work.
2. **Raw report text** — if the model passes the report body instead, each
   rule's `patterns` are matched against it directly.

Both paths end in the same normalised `{rule_id: value}` map before any rule is
evaluated, so the two cannot disagree about what was measured.

Unit handling stays deliberately narrow: rules declare a unit, patterns capture
the number, and a mismatched unit in the text is a `NO DATA` rather than a
silent conversion. Guessing at unit conversion is how a checker like this
produces a confidently wrong answer.

## Output contract

Markdown, matching the house style already set by `verify_sovereignty`:

```
## SOP assessment — SOP-MEC-014 — ATTENTION REQUIRED

**3 of 4 parameters within limits. 1 requires action.**

| Parameter | Measured | Acceptance limit | Clause | Verdict |
|---|---|---|---|---|
| Seal leakage | 3 to 4 drops/min | below 5 drops/min | §2.1 | PASS |
| Vibration | Zone B | Zone A or B | §3.1 | PASS |
| Wall thickness | 11.2 mm (1.7 mm margin) | above 9.5 mm retirement | §4.1 | PASS |
| Coupling guard | fastener missing (3 of 4) | no fastener missing | §5.1 | FAIL |

### Required actions
- **§5.1** — Rectify the missing coupling guard fastener before the next start.
- **§4.2** — Margin is 1.7 mm, below 2.0 mm: shorten the inspection interval to six months.

**Disposition: NOT FIT FOR START** until §5.1 is cleared.
```

Note the §4.2 row: a parameter can `PASS` its primary limit and still trigger a
secondary action. Actions are collected separately from verdicts for exactly
this reason.

The **Acceptance limit** column always shows the rule's acceptance criterion,
never the range of the band that happened to match. An earlier draft printed the
matched band — so a failing row read `up to 50 MOhm`, which scans as permission
rather than a breach. The clause reference already says which band applied.

The tool also states its own limitation in the footer, the way the sovereignty
tool does — it assesses only the parameters present in its rule pack and says so.

## Integration

- **Registered** in `install.py` as `ace_sop_check` / "4CE SOP Threshold Check",
  and enabled on the orchestrator model alongside the existing three.
- **Called by JARVIS** when producing an inspection deliverable. The docstring is
  written so the model reaches for it whenever a reading meets a limit.
- **Read by ULTRON** — the tool's table is deterministic ground truth, so a
  JARVIS conclusion that contradicts it is a clean, objective `FAIL` and a
  genuine trigger for the TONY replan. This is the first verification step in
  the system that does not rely on a model's opinion.
- **Feeds `deliverables.py`** — the actions list drops straight into an approval
  note body.

## Test plan

Added to `test_tools.py` as `test_sop_check`, following the existing shape:

| Check | Expectation |
|---|---|
| Demo report readings | Produces a table with 4 assessed parameters |
| Seal leakage 3–4 dpm | `PASS`, cites §2.1 |
| Seal leakage 12 dpm | `REVIEW`, cites §2.2, action mentions 30 days |
| Seal leakage 25 dpm | `FAIL`, cites §2.3, "remove from service" |
| Range input `3 to 4` | Assessed at 4, the worse end |
| Zone D vibration | `FAIL`, cites §3.3 |
| Wall thickness 11.2 vs 9.5 | `PASS` with a 1.7 mm margin, plus the §4.2 action |
| Missing guard fastener | `FAIL`, cites §5.1 |
| Rule with no reading | `NO DATA`, not `PASS` |
| Reading matching no rule | Listed as `NOT ASSESSED` |
| Empty input | Rejected with a clear message |
| Malformed rule pack JSON | Reports the parse error, does not fall back silently |

The whole suite runs without a database or a model server, unlike the other
three tools — the engine is pure functions over data.

## Deliberately out of scope

- **Learning thresholds from SOP prose.** Parsing an arbitrary SOP into rules
  with an LLM reintroduces the exact non-determinism this tool exists to remove.
  Rule packs are authored, reviewed and version-controlled.
- **Unit conversion.** See above.
- **Multi-SOP resolution.** One pack per call. Selecting the right SOP for a
  piece of equipment is a routing problem, not a threshold problem.
