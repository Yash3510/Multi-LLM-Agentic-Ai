# SOVEREIGN AI — STARK ARCHITECTURE

## SIH 2026 — Problem Statement 26117

> Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work.

## 1. Vision

Sovereign AI is a self-hosted, air-gapped Agentic AI Workbench for confidential industrial knowledge work.

The system is designed around four functional roles:

- **Tony Stark** — Chief Orchestrator
- **JARVIS** — Execution Agent
- **FRIDAY** — Analysis & Knowledge Agent
- **ULTRON** — Verification & Challenger Agent

The system runs local open-weight models, local tools, local storage, local OCR/vision, local knowledge retrieval and a sandboxed execution environment.

The core promise is:

> Confidential industrial work can be performed by a capable multi-agent AI system entirely inside the organization's infrastructure, without confidential data leaving the premises.

## 2. High-Level Architecture

```text
                         USER
                           |
                           v
                +----------------------+
                |    TONY STARK        |
                |    ORCHESTRATOR      |
                +----------+-----------+
                           |
                           v
                +----------------------+
                |     MODEL ROUTER      |
                |  Task -> Best Model   |
                +----------+-----------+
                           |
              +------------+------------+
              |            |            |
              v            v            v
         +---------+  +---------+  +---------+
         | JARVIS  |  | FRIDAY  |  | ULTRON  |
         | EXECUTE |  | ANALYZE |  | VERIFY  |
         +----+----+  +----+----+  +----+----+
              |            |            |
              +------------+------------+
                           |
                           v
                +----------------------+
                |    LOCAL TOOL LAYER  |
                +----------+-----------+
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
        LOCAL RAG       SANDBOX         OCR/VISION
          |                |                |
          +----------------+----------------+
                           |
                           v
                  VALIDATION LOOP
                           |
                    +------+------+
                    |             |
                  FAILED        PASSED
                    |             |
                    v             v
                  REPLAN      HUMAN REVIEW
                                  |
                                  v
                           FINAL DELIVERABLE
                                  |
                                  v
                            AUDIT LOG
```

## 3. System Layers

### Presentation Layer
- Web application
- Chat
- Workspace
- Files
- Knowledge Base
- Agent activity
- Model management
- Audit
- Sovereign security dashboard

### API Layer
- Authentication
- Conversations
- Files
- Tasks
- Agents
- Models
- Tools
- Knowledge
- Approvals
- Audit

### Orchestration Layer
- Tony task analysis
- Planning
- Routing
- Agent coordination
- State management
- Retry/replanning

### Agent Layer
- JARVIS
- FRIDAY
- ULTRON

### Model Layer
Provider-independent interface for local inference engines.

### Tool Layer
- Files
- OCR
- RAG
- Calculator
- Sandbox
- Documents
- Spreadsheets
- Presentations

### Knowledge Layer
- Parsers
- OCR
- Chunking
- Embeddings
- Vector database
- Retrieval
- Citations

### Security Layer
- Air-gap mode
- Network controls
- Sandbox isolation
- Secrets protection
- Audit logging

### Storage Layer
- Relational database
- Object/file storage
- Vector database
- Audit records

## 4. Core Data Flow

```text
USER REQUEST
    |
    v
TASK CLASSIFICATION
    |
    v
PLAN
    |
    v
MODEL SELECTION
    |
    v
AGENT SELECTION
    |
    v
TOOL EXECUTION
    |
    v
RESULT
    |
    v
ULTRON VERIFICATION
    |
    +---- FAIL ----> TONY REPLAN
    |
    +---- PASS ----> HUMAN REVIEW
                         |
                         v
                    DELIVERABLE
                         |
                         v
                       AUDIT
```

## 5. Sovereignty Principle

No core workflow depends on:
- Cloud LLMs
- Cloud OCR
- Cloud embeddings
- External analytics
- External telemetry
- External search

The production deployment must be capable of operating without Internet connectivity.

## 6. Primary SIH Demonstration

### Industrial inspection workflow

```text
Scanned Inspection Report
        |
        v
OCR + Vision
        |
        v
FRIDAY
        |
        +--> Local Knowledge Base
        |
        v
Extract Findings
        |
        v
JARVIS
        |
        v
Approval Note DOCX
        |
        v
ULTRON
        |
        v
Human Approval
        |
        v
Final Deliverable
```

### Coding workflow

```text
Coding Request
      |
      v
Tony
      |
      v
JARVIS
      |
      v
Code Generation
      |
      v
Sandbox
      |
      v
Tests
      |
      v
ULTRON
      |
      v
Verified Code
```

## 7. Non-Goals

The SIH prototype should not prioritize:
- Large numbers of cloud integrations
- Consumer social features
- Unnecessary autonomous actions
- Features that compromise offline operation
- UI effects over reliability

## 8. Acceptance Criteria

- Fully local deployment
- Multiple open-weight models
- Automatic model routing
- Multi-agent execution
- OCR/vision
- Local RAG
- Sandboxed code execution
- Real document generation
- Verification and replanning
- Human approval
- Auditability
- Demonstrable zero external calls
- Docker deployment
