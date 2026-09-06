# Phase 2 — Stark Multi-Agent Runtime

## Objective

Turn the foundation into a real multi-agent execution system.

## Architecture

```text
USER
 |
 v
TONY STARK
 |
 v
MODEL ROUTER
 |
 +---- JARVIS
 +---- FRIDAY
 +---- ULTRON
 |
 v
RESULT
```

## Tony Stark — Orchestrator

Responsibilities:
- Understand request
- Classify task
- Build plan
- Select agent
- Select model
- Select tools
- Maintain task state
- Handle failures
- Trigger verification
- Request approval

Tony returns structured plans.

Example:

```json
{
  "task": "Analyze inspection report",
  "steps": [
    {"agent": "friday", "action": "analyze_document"},
    {"agent": "jarvis", "action": "generate_document"},
    {"agent": "ultron", "action": "verify"}
  ]
}
```

## JARVIS — Execution

Responsibilities:
- File operations
- Calculations
- Data processing
- Structured execution
- Tool invocation

No unrestricted host execution.

## FRIDAY — Analysis

Responsibilities:
- Document analysis
- Information extraction
- Context analysis
- Knowledge retrieval interface

## ULTRON — Verification

Responsibilities:
- Result review
- Validation
- Contradiction detection
- Confidence assessment

ULTRON must challenge results rather than automatically approve them.

## Agent Interface

```text
Agent
├── plan()
├── execute()
├── validate()
├── status()
└── result()
```

## Task Engine

Track:
- Task ID
- User
- Status
- Plan
- Current step
- Agent
- Model
- Tool
- Input
- Output
- Verification
- Audit events

## UI

Show real execution state:

```text
Tony Stark
✓ Task understood

Tony Stark
✓ Plan created

Friday
● Analyzing

Jarvis
○ Waiting

Ultron
○ Waiting
```

Do not fake activity.

## Acceptance Test

Demonstrate:

```text
User
 ↓
Tony creates plan
 ↓
Friday analyzes
 ↓
Jarvis executes
 ↓
Ultron verifies
 ↓
Final result
```

Test retries and failures.
