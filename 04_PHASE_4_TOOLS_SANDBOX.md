# Phase 4 — Tools, Sandbox & Deliverables

## Objective

Give agents safe access to useful local tools.

## Tool Architecture

```text
TONY
 ↓
AGENT
 ↓
TOOL REGISTRY
 ↓
LOCAL TOOL
 ↓
RESULT
 ↓
AGENT
```

## Initial Tools

### File
- Read
- Write
- Move
- Copy
- Create directory
- Search

### Documents
- PDF parser
- DOCX reader
- DOCX generator
- PPTX generator
- XLSX generator

### Data
- CSV processing
- Spreadsheet calculations
- Data analysis

### Calculator
Use deterministic calculation functions where possible.

### Code Sandbox

Generated code must NEVER execute directly on the host.

Sandbox requirements:
- Restricted filesystem
- Resource limits
- Timeout
- Process isolation
- No secrets
- No network

## Tool Registry

Each tool defines:

```text
name
description
input_schema
execute()
permissions
risk_level
```

## Permissions

LOW:
- Read
- Search

MEDIUM:
- Generate
- Modify

HIGH:
- Execute code
- Delete

High-risk operations can require approval.

## Deliverables

Generate:
- DOCX
- XLSX
- PPTX
- CSV
- TXT
- Source code

## JARVIS

JARVIS is the primary tool execution agent.

Example:

```text
Read PDF
 ↓
Extract data
 ↓
Calculate
 ↓
Generate Excel
 ↓
Verify
```

## Audit

Log every invocation:
- Timestamp
- Task
- Agent
- Tool
- Input
- Result
- Duration
- Status

## Acceptance Tests

### Dataset workflow

```text
Dataset
 ↓
Read
 ↓
Calculate
 ↓
Generate XLSX
 ↓
Verify
```

### Coding workflow

```text
Request
 ↓
Generate Python
 ↓
Sandbox
 ↓
Execute
 ↓
Test
 ↓
ULTRON
```

Sandbox must have no network access.
