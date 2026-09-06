# Phase 5 — Verification & Human-in-the-Loop

## Objective

Make verification a formal part of every appropriate agentic workflow.

## Validation Loop

```text
TASK
 ↓
PLAN
 ↓
EXECUTE
 ↓
VERIFY
 ↓
 +---- FAIL ----> REPLAN
 |
 +---- PASS ----> HUMAN REVIEW
                         |
                         v
                      APPROVE
                         |
                         v
                    FINAL OUTPUT
```

## ULTRON

ULTRON receives:
- Original task
- Plan
- Evidence
- Tool outputs
- Generated result

Evaluate:
- Factual consistency
- Evidence support
- Calculation correctness
- Missing information
- Contradictions
- Risks
- Completeness

Structured result:

```json
{
  "status": "PASS",
  "confidence": 0.91,
  "issues": [],
  "warnings": [],
  "evidence": [],
  "recommendation": "approve"
}
```

Statuses:
- PASS
- FAIL
- NEEDS_REVIEW
- WARNING

## Replanning

```text
ULTRON
 ↓
FAIL
 ↓
TONY
 ↓
REPLAN
 ↓
AGENT
 ↓
VERIFY AGAIN
```

Use bounded retries.

## Human Approval

Display:
- Task
- Result
- Sources
- Verification
- Warnings
- Confidence
- Generated files
- Activity

Actions:
- Approve
- Request changes
- Reject

## Approval Policy

Examples:
- Normal analysis: automatic
- Generated report: review recommended
- Sensitive recommendation: approval required
- File deletion: approval required

## Audit

Record:
- Approver
- Time
- Decision
- Output version
- Requested changes

## Important

Do not expose private chain-of-thought.

Show concise reasoning summaries, evidence, actions and verification results.

## Acceptance Tests

1. Introduce an intentionally incorrect result.
2. ULTRON must detect it.
3. Tony must replan.
4. Verify again.

Then complete a valid task requiring human approval and ensure final approval status changes only after the human action.
