# Phase 4 — Tools, Sandbox, Agent Workflow & Deliverables

**Series:** [Docs index](../README.md) · ← [Phase 3](03_PHASE_3_INDUSTRIAL_AI.md) · **Phase 4** → [Phase 5](05_PHASE_5_VERIFICATION.md) · [Verification](../verification/PHASE_4_VERIFICATION.md)

## Objective

Extend the existing Sovereign AI system with safe local tools, sandboxed execution, real deliverable generation, and reliable multi-step agent workflows.

Phases 1–3 are already substantially implemented.

Do NOT redesign or replace the existing:

* Tkinter UI
* Tony Stark orchestrator
* FRIDAY
* JARVIS
* ULTRON
* Bionic local model infrastructure
* Turbovec RAG infrastructure

This phase should integrate mature, well-maintained open-source components where they provide real value instead of unnecessarily reimplementing established functionality.

The system must remain fully self-hosted and suitable for the SIH sovereign/on-premise requirement.

---

# 1. EXISTING ARCHITECTURE

The current system uses:

```text
TKINTER
   ↓
TONY STARK
   ↓
FRIDAY / JARVIS / ULTRON
   ↓
BIONIC
   ↓
LOCAL LLMs / EMBEDDING / VISION MODELS
```

Phase 4 must preserve this architecture.

The final architecture should become:

```text
                         TKINTER
                            │
                            ▼
                         TONY
                    APPLICATION ROUTER
                            │
                            ▼
                       LANGGRAPH
                 WORKFLOW / TASK STATE
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           FRIDAY        JARVIS        ULTRON
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ▼
                         BIONIC
                   LOCAL MODEL GATEWAY
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           Local LLM     Embeddings      Vision
                            │
                            ▼
                         TURBOVEC
```

Responsibilities must remain clearly separated.

---

# 2. BIONIC INTEGRATION

Bionic is the local model hosting/gateway layer.

Do NOT replace Bionic with LangGraph.

Do NOT make LangGraph responsible for hosting models.

Do NOT move model inference into LangGraph.

Bionic should continue to provide access to locally hosted models.

Where supported by the existing Bionic configuration, use its OpenAI-compatible local API interface.

The application should communicate with Bionic through a dedicated adapter.

Example:

```text
Tony / LangGraph
       ↓
BionicAdapter
       ↓
Bionic
       ↓
Selected Local Model
```

Create or reuse an abstraction such as:

```python
class LocalModelProvider:
    def generate(...)
    def stream(...)
    def embed(...)
    def vision(...)
```

Then implement:

```text
LocalModelProvider
        ↓
BionicProvider
        ↓
Bionic local API
```

Do not scatter Bionic-specific API calls throughout the agent code.

This allows the local model infrastructure to remain replaceable.

---

# 3. LANGGRAPH INTEGRATION

Use LangGraph only where it improves the existing multi-step orchestration.

LangGraph must NOT replace Tony.

Tony remains the application's primary orchestrator and routing layer.

LangGraph should provide:

* workflow state
* multi-step execution
* branching
* retries
* checkpoints where useful
* resumable tasks where useful
* human approval interruptions
* agent/tool transitions
* structured execution state

Expected relationship:

```text
TKINTER
   ↓
TONY
   ↓
Create / select workflow
   ↓
LANGGRAPH
   ↓
FRIDAY / JARVIS / ULTRON
```

Do not create a second competing orchestrator.

Tony decides what workflow should happen.

LangGraph manages execution state and transitions within that workflow.

---

# 4. LANGGRAPH + BIONIC

There must be a clean boundary:

```text
LANGGRAPH
    │
    │ model invocation
    ▼
BIONIC ADAPTER
    │
    ▼
BIONIC
    │
    ▼
LOCAL MODEL
```

LangGraph must not:

* download models
* host models
* manage GPU memory directly
* call cloud LLM providers
* bypass Bionic for inference

All model calls must remain local.

If the Bionic endpoint is OpenAI-compatible, use the appropriate OpenAI-compatible client/adapter.

If Bionic requires a project-specific adapter, implement one.

Do not hard-code model names throughout the workflow.

---

# 5. MODEL SELECTION

Tony remains responsible for model selection.

The workflow should be able to receive a selected model/provider from Tony.

Example:

```text
User Task
   ↓
Tony
   ↓
Task classification
   ↓
Model selection
   ↓
Bionic
   ↓
Local model
```

Examples:

```text
Coding
→ coding-capable local model

Document reasoning
→ reasoning-capable local model

Vision
→ local vision-capable model

Embedding
→ local embedding model
```

Do not allow LangGraph to randomly choose models independently of Tony's routing policy.

The selected model should be visible in logs/UI where appropriate.

---

# 6. TOOL ARCHITECTURE

Implement:

```text
TONY
  ↓
LANGGRAPH WORKFLOW
  ↓
AGENT
  ↓
TOOL REGISTRY
  ↓
LOCAL TOOL
  ↓
RESULT
  ↓
LANGGRAPH STATE
  ↓
AGENT
```

Tools must be explicit registered capabilities.

Do not allow agents to execute arbitrary Python functions.

---

# 7. TOOL REGISTRY

Each tool must define:

```text
name
description
input_schema
execute()
permissions
risk_level
timeout
```

Example:

```python
Tool(
    name="read_file",
    description="Read an approved local file",
    input_schema={...},
    permissions=["read"],
    risk_level="LOW",
    timeout=10
)
```

The registry should support:

```text
register_tool()
get_tool()
list_tools()
validate_input()
check_permission()
execute_tool()
```

All tool executions should pass through the registry.

---

# 8. INITIAL TOOLS

Implement the following tools using mature standard/open-source libraries where appropriate.

## File Tools

* Read
* Write
* Move
* Copy
* Create directory
* Search

Use safe filesystem APIs.

Do not allow tools to escape their permitted working directories.

---

# 9. DOCUMENT TOOLS

Use mature open-source libraries rather than reimplementing document formats.

Support:

* PDF parsing
* DOCX reading
* DOCX generation
* PPTX generation
* XLSX generation

Recommended libraries may include:

```text
pypdf / equivalent local PDF library
python-docx
python-pptx
openpyxl
```

Use the existing project dependencies if equivalent functionality is already implemented.

Do not add duplicate libraries unnecessarily.

---

# 10. DATA TOOLS

Support:

* CSV processing
* Spreadsheet calculations
* Data analysis
* Basic tabular transformations

Use established local libraries such as pandas where appropriate.

All calculations must happen locally.

---

# 11. CALCULATOR

Provide deterministic calculation tools where possible.

For numerical operations:

```text
User
 ↓
Calculator Tool
 ↓
Deterministic Result
```

Do not rely on an LLM to perform arithmetic when deterministic computation is available.

For complex calculations, preserve intermediate steps where useful.

---

# 12. CODE SANDBOX

Generated code must NEVER execute directly on the host.

The execution architecture must be:

```text
JARVIS
   ↓
Generate code
   ↓
LANGGRAPH STATE
   ↓
SANDBOX MANAGER
   ↓
DOCKER CONTAINER
   ↓
Execute
   ↓
Capture stdout/stderr
   ↓
Return result
   ↓
ULTRON
```

Use Docker as the local sandbox/isolation mechanism.

Do not use an external/cloud sandbox service.

Do not use E2B or another hosted execution service because this project
must remain sovereign and locally executable.

---

# 13. SANDBOX REQUIREMENTS

The sandbox must provide, as far as practical:

* Restricted filesystem
* Temporary workspace
* Resource limits
* CPU limits
* Memory limits
* Execution timeout
* Process isolation
* No secrets
* No host filesystem access
* No network access
* Controlled working directory
* Captured stdout
* Captured stderr
* Exit code
* Cleanup after execution

The sandbox must not inherit sensitive host environment variables.

Never mount the user's home directory into the sandbox.

Never expose application secrets to generated code.

---

# 14. NETWORK ISOLATION

The code sandbox must have no network access.

Test explicitly.

Example:

```text
Generated code
      ↓
attempt network request
      ↓
NETWORK BLOCKED
```

Do not simply assume Docker isolation means network isolation.

Explicitly configure the sandbox network policy.

Acceptance condition:

```text
Network access from sandbox = BLOCKED
```

---

# 15. RESOURCE LIMITS

Set practical limits for:

```text
CPU
Memory
Execution time
Output size
Filesystem size
```

Prevent infinite loops from running forever.

Example:

```text
Timeout:
30 seconds

Memory:
configurable

CPU:
configurable

Output:
configurable
```

Use configuration rather than hard-coded values where practical.

---

# 16. TOOL PERMISSIONS

Define:

### LOW

* Read
* Search
* Inspect metadata

### MEDIUM

* Generate
* Modify
* Create files

### HIGH

* Execute code
* Delete files
* Move files outside the current workspace

High-risk operations should require approval when appropriate.

Permission checks must happen before execution.

---

# 17. HUMAN APPROVAL

Integrate approval into the LangGraph workflow where useful.

Example:

```text
JARVIS
  ↓
Requests high-risk tool
  ↓
LANGGRAPH INTERRUPT
  ↓
TONY
  ↓
TKINTER APPROVAL UI
  ↓
User approves/rejects
  ↓
LANGGRAPH RESUMES
  ↓
Tool executes or task stops
```

The application must never bypass a required approval.

---

# 18. DELIVERABLES

Agents must be able to generate real local files:

* DOCX
* XLSX
* PPTX
* CSV
* TXT
* Source code

Generated files must be saved to an explicit workspace.

Return:

```text
file_path
file_type
file_size
creation_time
task_id
```

The Tkinter UI should allow the user to locate/open the generated
deliverable where supported.

---

# 19. JARVIS

JARVIS remains the primary tool-execution agent.

Example workflow:

```text
User
 ↓
Tony
 ↓
LangGraph
 ↓
JARVIS
 ↓
Read PDF
 ↓
Extract data
 ↓
Calculate
 ↓
Generate XLSX
 ↓
ULTRON
 ↓
Verify
 ↓
Final XLSX
```

JARVIS should not directly bypass the Tool Registry.

All tool calls must go through the registered tool system.

---

# 20. ULTRON VERIFICATION

After important tool operations, ULTRON should be able to verify:

* output exists
* output is readable
* calculations are consistent
* generated files are structurally valid
* expected fields are present
* code execution succeeded
* test results are correct
* output matches task requirements

Example:

```text
JARVIS
 ↓
Generate XLSX
 ↓
ULTRON
 ↓
Open generated XLSX
 ↓
Validate sheets
 ↓
Validate formulas/data
 ↓
PASS / FAIL
```

If verification fails:

```text
ULTRON
 ↓
FAIL
 ↓
LANGGRAPH
 ↓
Return to JARVIS
 ↓
Correct
 ↓
Verify again
```

Do not create infinite retry loops.

Set a maximum retry count.

---

# 21. AUDIT LOGGING

Log every important tool invocation.

Minimum fields:

```text
Timestamp
Task ID
Agent
Tool
Risk level
Input summary
Result summary
Duration
Status
Approval state
Error
```

Do not log sensitive file contents unnecessarily.

Prefer hashes, identifiers, paths, summaries, and metadata.

For example:

```text
Task: task_042
Agent: JARVIS
Tool: generate_xlsx
Risk: MEDIUM
Status: SUCCESS
Duration: 3.4s
Output: report.xlsx
```

---

# 22. TOOL FAILURE HANDLING

Every tool must return structured success/failure information.

Example:

```json
{
  "success": false,
  "tool": "execute_python",
  "error": "Execution timed out",
  "duration_ms": 30000
}
```

Agents must be able to reason about tool failures.

Do not convert every failure into a fake successful result.

---

# 23. LANGGRAPH STATE

Define a clear workflow state.

At minimum include:

```text
task_id
user_request
current_agent
selected_model
current_step
tool_calls
tool_results
artifacts
verification_results
approval_state
errors
retry_count
final_status
```

Do not put huge document contents or binary files unnecessarily into
workflow state.

Store large artifacts in local storage and reference them by ID/path.

---

# 24. AGENT WORKFLOW EXAMPLE

Implement/support workflows such as:

```text
User
 ↓
Tony
 ↓
Create task
 ↓
LangGraph
 ↓
Select agent
 ↓
JARVIS
 ↓
Tool Registry
 ↓
Tool
 ↓
Result
 ↓
LangGraph state
 ↓
ULTRON
 ↓
PASS?
 ├── YES → Complete
 └── NO  → Retry/replan
```

The workflow must terminate cleanly.

---

# 25. DATASET ACCEPTANCE TEST

Create a controlled local dataset.

Workflow:

```text
Dataset
   ↓
JARVIS
   ↓
Read
   ↓
Calculate
   ↓
Generate XLSX
   ↓
ULTRON
   ↓
Verify
```

Verify:

* input read correctly
* calculations are correct
* XLSX generated
* workbook opens successfully
* expected sheets exist
* expected values exist
* ULTRON verifies the output

---

# 26. CODING ACCEPTANCE TEST

Workflow:

```text
User Request
      ↓
Tony
      ↓
LangGraph
      ↓
JARVIS
      ↓
Generate Python
      ↓
Docker Sandbox
      ↓
Execute
      ↓
Run Tests
      ↓
ULTRON
      ↓
Verify
      ↓
Result
```

The generated code must execute only inside the sandbox.

Test explicitly that:

```text
Sandbox network = BLOCKED
Sandbox cannot access host secrets
Sandbox cannot access host filesystem
Sandbox terminates after timeout
```

---

# 27. DOCUMENT DELIVERABLE ACCEPTANCE TEST

Use an existing local document from the Phase 3 test dataset.

Example:

```text
Inspection Report
       ↓
FRIDAY
       ↓
Extract findings
       ↓
JARVIS
       ↓
Generate approval note DOCX
       ↓
ULTRON
       ↓
Validate DOCX
       ↓
Tkinter
       ↓
Display generated document
```

The output must be a real `.docx` file.

---

# 28. TKINTER INTEGRATION

The Tkinter application is the official user interface.

Add/verify UI support for:

* task submission
* task progress
* agent activity
* tool activity
* approval requests
* generated artifacts
* errors
* verification results

Example:

```text
┌─────────────────────────────────────┐
│ Task: Inspection Report Analysis    │
├─────────────────────────────────────┤
│ ✓ Tony      Planned task            │
│ ✓ FRIDAY    Retrieved evidence      │
│ ✓ JARVIS    Generated DOCX          │
│ → ULTRON    Verifying document      │
│                                     │
│ Status: VERIFYING                   │
└─────────────────────────────────────┘
```

Do not block the Tkinter main event loop.

Long-running workflows must execute asynchronously.

---

# 29. BIONIC + LANGGRAPH ACCEPTANCE TEST

Create a specific integration test proving that LangGraph and Bionic
work together correctly.

Test:

```text
Tkinter
 ↓
Tony
 ↓
LangGraph
 ↓
Bionic Adapter
 ↓
Bionic
 ↓
Local Model
 ↓
Response
 ↓
LangGraph
 ↓
Tony
 ↓
Tkinter
```

Verify:

* correct model selected
* request reaches Bionic
* local model generates response
* response returns to workflow
* workflow continues
* no external provider is contacted

Also test switching between two locally available models if the
current Bionic configuration supports multiple models.

---

# 30. BIONIC FAILURE TEST

Simulate Bionic/local-model unavailability.

Expected:

```text
Bionic unavailable
      ↓
Model invocation fails
      ↓
LangGraph captures failure
      ↓
Tony receives failure
      ↓
Tkinter displays meaningful error
```

Do not crash the application.

Do not silently switch to a cloud model.

---

# 31. TOOL REGISTRY TESTS

Test:

```text
Register tool
 ↓
Discover tool
 ↓
Validate schema
 ↓
Check permissions
 ↓
Execute
 ↓
Return structured result
 ↓
Audit
```

Also test unauthorized execution.

Example:

```text
LOW permission agent
      ↓
attempt HIGH-risk tool
      ↓
DENIED
```

---

# 32. SANDBOX TESTS

Create automated tests for:

1. Python execution
2. Successful execution
3. Failed execution
4. Timeout
5. Memory/resource limit
6. Filesystem restriction
7. Secret isolation
8. Network isolation
9. Container cleanup

The network test is mandatory.

---

# 33. DELIVERABLE TESTS

Verify:

```text
DOCX → opens successfully
XLSX → opens successfully
PPTX → opens successfully
CSV  → valid CSV
TXT  → readable
Code → syntactically valid where applicable
```

Do not merely check that a file exists.

Validate its structure/content.

---

# 34. NO CLOUD DEPENDENCIES

This phase must not introduce:

* OpenAI API
* Anthropic API
* Gemini API
* hosted sandbox services
* cloud code execution
* cloud document generation
* cloud OCR
* cloud embeddings
* external telemetry

Bionic must remain configured for local model execution.

LangGraph must only orchestrate the local components.

---

# 35. SECURITY PRINCIPLE

The complete Phase 4 architecture must remain:

```text
                TKINTER
                   │
                   ▼
                 TONY
                   │
                   ▼
              LANGGRAPH
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     FRIDAY     JARVIS      ULTRON
        │          │          │
        └──────────┼──────────┘
                   ▼
                BIONIC
                   │
                   ▼
             LOCAL MODELS
                   │
                   ├──── RAG → TURBOVEC
                   │
                   └──── TOOLS
                           │
                           ▼
                       DOCKER
                       SANDBOX
```

Nothing in this workflow should require an external network connection.

---

# 36. IMPLEMENTATION STRATEGY

Before implementing a new component:

1. Inspect existing implementation.
2. Determine whether functionality already exists.
3. Identify whether a mature open-source library can safely provide
   the missing capability.
4. Prefer established libraries for file formats and infrastructure.
5. Integrate them behind your own interfaces.
6. Avoid framework lock-in.
7. Keep Tony/JARVIS/FRIDAY/ULTRON as your application's architecture.

Do not add LangGraph merely because it is popular.

Use it only for workflow/state/orchestration functionality that improves
the current implementation.

---

# 37. RECOMMENDED COMPONENT BOUNDARIES

Use:

```text
Tkinter
→ UI

Tony
→ Application orchestration / routing

LangGraph
→ Workflow state / transitions / checkpoints / interrupts

Bionic
→ Local LLM / embedding / vision model gateway

FRIDAY
→ RAG / research / document analysis

JARVIS
→ Tool execution

ULTRON
→ Verification

Turbovec
→ Vector retrieval

Docker
→ Code sandbox

python-docx
→ DOCX

openpyxl
→ XLSX

python-pptx
→ PPTX

pandas
→ CSV/data analysis
```

Do not let one framework absorb responsibilities belonging to another
component.

---

# 38. FINAL ACCEPTANCE CRITERIA

Phase 4 is complete when the system can demonstrate:

### Tool execution

```text
Tony
 ↓
LangGraph
 ↓
JARVIS
 ↓
Tool Registry
 ↓
Local Tool
 ↓
Result
```

### Code execution

```text
JARVIS
 ↓
Docker Sandbox
 ↓
Execute
 ↓
ULTRON
 ↓
Verify
```

### Deliverable generation

```text
Input
 ↓
Agent
 ↓
Tool
 ↓
DOCX/XLSX/PPTX/CSV/TXT
 ↓
ULTRON
 ↓
Verified Artifact
```

### Human approval

```text
High-risk tool
 ↓
Approval request
 ↓
Tkinter
 ↓
User
 ↓
Approve/Reject
 ↓
Workflow resumes/stops
```

### Local model execution

```text
LangGraph
 ↓
Bionic
 ↓
Local model
 ↓
Result
```

### Sovereignty

```text
Cloud LLM             BLOCKED
Cloud OCR             BLOCKED
Cloud embeddings      BLOCKED
External sandbox      BLOCKED
Sandbox network       BLOCKED
External telemetry    BLOCKED
```

==================================================
FINAL OUTPUT
============

After implementation, provide:

1. Files changed
2. Files added
3. Libraries/repositories integrated
4. Why each library was selected
5. Bugs fixed
6. Tools implemented
7. Sandbox implementation
8. LangGraph integration
9. Bionic integration
10. Tests added
11. Commands used for verification
12. Dataset workflow result
13. Coding workflow result
14. Deliverable workflow result
15. Security/network test result
16. Phase 4 remaining limitations
17. Exact next steps

For every component clearly state:

```text
Implemented
Tested
Partially Tested
Not Verified
Unsupported
```

Do not claim Phase 4 is complete until the acceptance tests actually pass.
