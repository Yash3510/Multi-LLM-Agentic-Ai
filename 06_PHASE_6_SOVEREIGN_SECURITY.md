# Phase 6 — Sovereign Security & Air-Gapped Runtime

## Objective

Technically enforce and visibly demonstrate the sovereign claim.

"Offline" must not be a marketing label.

## Sovereign Mode

When enabled:
- External network access disabled
- Cloud AI disabled
- External OCR disabled
- External embeddings disabled
- External telemetry disabled
- External analytics disabled
- External search disabled

Local functionality must continue.

## Network Policy

Unauthorized outbound requests must be:
1. Blocked
2. Logged
3. Shown as security events

The system should fail safely.

## Security Dashboard

Show real system/network state where possible:

```text
SOVEREIGN SECURITY

Internet Access       BLOCKED
External APIs         BLOCKED
Cloud LLMs            BLOCKED
External OCR          BLOCKED
External Embeddings   BLOCKED
Telemetry             BLOCKED

External Requests:    0
Data Transferred:     0 B
```

Do not fabricate counters.

## Audit

Record:
- User
- Task
- Agent
- Model
- Tool
- File
- Timestamp
- Action
- Result
- Approval
- Security event

## Model Audit

Record:
- Model
- Provider
- Local/External
- Task
- Timestamp
- Duration
- Token usage when available

## Data Flow

```text
USER
 ↓
TONY
 ↓
LOCAL AGENTS
 ↓
LOCAL MODELS
 ↓
LOCAL TOOLS
 ↓
LOCAL STORAGE

      X INTERNET
```

## Secret Protection

Ensure:
- Secrets never appear in logs
- Secrets are not exposed to generated code
- Environment variables hold configuration
- Sensitive values are excluded from prompts where possible

## Sandbox Isolation

Generated code must have no network access.

Explicitly test this.

## Offline Test

Disconnect Internet.

Verify:
- Chat
- RAG
- OCR
- Vision where locally supported
- Agents
- Sandbox
- Document generation
- Verification
- Audit

## External Request Test

Attempt an external request.

Expected:

```text
REQUEST
 ↓
BLOCK
 ↓
AUDIT EVENT
 ↓
SECURITY ALERT
```

## Acceptance Criteria

A live demonstration must be possible with the machine disconnected from the Internet.

The security dashboard and logs must provide evidence of zero external calls.
