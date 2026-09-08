# Phase 3 — Industrial Document AI & Local RAG

**Series:** [Docs index](../README.md) · ← [Phase 2](02_PHASE_2_STARK_AGENTS.md) · **Phase 3** → [Phase 4](04_PHASE_4_TOOLS_SANDBOX.md) · [Verification](../verification/PHASE_1_3_VERIFICATION.md)

## Objective

Build the local multimodal document intelligence and organizational knowledge layer for the Sovereign AI system.

This phase gives FRIDAY access to a searchable local knowledge base containing industrial documents, manuals, SOPs, inspection reports, correspondence, engineering documents, and other confidential organizational information.

Everything must run locally. No document, embedding, OCR result, query, or retrieved content may leave the machine.

1. Document Intelligence Pipeline

Implement the following pipeline:

FILE
  ↓
INGESTION
  ↓
FILE TYPE DETECTION
  ↓
PARSER / OCR / VISION
  ↓
TEXT + STRUCTURE EXTRACTION
  ↓
CHUNKING
  ↓
LOCAL EMBEDDINGS
  ↓
TURBOVEC VECTOR INDEX
  ↓
METADATA / DOCUMENT STORE
  ↓
RETRIEVAL
  ↓
OPTIONAL LOCAL RERANKING
  ↓
FRIDAY
  ↓
LOCAL LLM
  ↓
EVIDENCE-GROUNDED RESPONSE

The implementation must be modular so individual components can be replaced without rewriting the entire RAG system.

2. Document Ingestion

Support the following formats:

PDF
Scanned PDF
DOCX
XLSX
PPTX
TXT
CSV
PNG
JPG/JPEG
Other common image formats where practical

For every uploaded document, extract and store:

Document ID
Filename
File type
File size
Upload timestamp
Modified timestamp
Checksum / content hash
Page count where applicable
Processing status
Processing errors
Version

Use the checksum to detect duplicate files and unnecessary re-processing.

3. Document Parsing

Use local parsers only.

The ingestion system should determine whether a document contains:

Normal text
Scanned pages
Images
Tables
Mixed text/image content

Normal machine-readable documents should be parsed directly without unnecessary OCR.

For example:

PDF
 ↓
Can extract text?
 ├── YES → Text Parser
 │
 └── NO → Local OCR

For mixed documents:

PDF
 ↓
Page Analysis
 ↓
Text Pages → Parser
Image Pages → OCR / Vision
 ↓
Unified Document Representation
4. Local OCR

Implement local OCR for scanned documents.

Requirements:

Automatic scanned-document detection
Page-level OCR
Preserve page numbers
Preserve document structure where possible
Store OCR confidence where available
Never send documents to cloud OCR services

OCR output must remain available for later retrieval and citation.

Example:

Scanned PDF
     ↓
Local OCR
     ↓
Page 1 → Text
Page 2 → Text
Page 3 → Text
     ↓
Chunking
     ↓
Embeddings
5. Local Vision

Support local vision-capable models for:

Images
Scanned documents
Tables
Diagrams
Charts
Photographs
Engineering drawings where supported
P&IDs where supported

Vision processing must be performed using locally hosted models.

The system should preserve the relationship between visual information and its original document/page.

Example:

Engineering Drawing
       ↓
Local Vision Model
       ↓
Visual Description
       ↓
Document/Page Metadata
       ↓
Retrieval System

Do not claim that an engineering drawing was understood correctly unless the selected vision model actually supports the required analysis.

6. Document Structure

Do not treat every document as an undifferentiated block of text.

Where possible, preserve:

Document
 ├── Page
 │    ├── Section
 │    ├── Paragraph
 │    ├── Table
 │    ├── Image
 │    └── Diagram

Each extracted piece should maintain its source location.

Example chunk:

{
  "chunk_id": "chunk_001",
  "document_id": "doc_042",
  "page": 17,
  "section": "Pump Maintenance",
  "content": "...",
  "source": "maintenance_manual.pdf"
}
7. Chunking

Implement configurable document chunking.

Chunks should contain enough context to be meaningful while remaining suitable for embedding and retrieval.

Store metadata alongside every chunk:

Chunk ID
Document ID
Document version
Page
Section
Paragraph / block
Source filename
Timestamp
Content hash

Avoid splitting important tables, procedures, headings, or structured information unnecessarily.

8. Local Embeddings

Use local embedding models only.

Requirements:

No OpenAI embedding API
No cloud embedding service
No external API dependency
Embeddings generated entirely on the local machine/server

The embedding system must be configurable so different local embedding models can be tested.

Example:

Document Chunk
      ↓
Local Embedding Model
      ↓
Embedding Vector
      ↓
Turbovec

Store the embedding model/version used for each index so the system knows when re-indexing is required.

9. Vector Index — Turbovec

Use Turbovec as the primary local vector index for this implementation.

Repository:

RyanCodrai/turbovec

Turbovec should handle the vector similarity-search layer of the RAG system.

It should not be treated as the complete document database.

Architecture:

                 DOCUMENT
                    ↓
              Chunk + Metadata
                    ↓
             Local Embeddings
                    ↓
              ┌─────────────┐
              │  TURBOVEC   │
              │ Vector Index│
              └─────────────┘
                    ↓
             Candidate Chunks
                    ↓
              Metadata Store
                    ↓
              Full Chunk Data

Use Turbovec for:

Vector storage/indexing
Similarity search
Incremental ingestion
Fast local retrieval
Stable external IDs where appropriate
Search-time filtering/allowlists where appropriate

Use a separate local metadata/document store for:

Original document metadata
Full extracted text
Chunk content
Page information
Section information
Document versions
Permissions
Processing status
Audit information

Do not store the entire organizational document-management system inside the vector index.

10. Vector Store Abstraction

Create a clean interface around the vector index.

Example:

class VectorStore:
    def add(self, vectors, metadata):
        pass

    def search(self, query_vector, top_k):
        pass

    def delete(self, ids):
        pass

    def update(self, ids, vectors):
        pass

    def save(self):
        pass

    def load(self):
        pass

Implement:

VectorStore
    ↓
TurbovecVectorStore

This keeps the architecture modular and allows another vector index to be introduced later without changing FRIDAY or the RAG pipeline.

11. Stable Document and Chunk IDs

Use stable IDs for documents and chunks.

Recommended structure:

document_id
    ↓
document_version
    ↓
chunk_id
    ↓
vector_id

Turbovec's stable external-ID functionality should be used where appropriate so retrieved vectors can reliably map back to the corresponding chunk/document records.

Never rely solely on vector position or array index as a permanent identifier.

12. Metadata Filtering

The retrieval layer should support metadata filtering where required.

Examples:

Department = Mechanical
Document Type = SOP
Year = 2025
Equipment = Compressor
Document Version = Latest

Example:

Question
   ↓
Query Embedding
   ↓
Turbovec Search
   ↓
Metadata Filtering
   ↓
Relevant Chunks

This is particularly important for large organizational knowledge bases.

13. RAG Pipeline

Implement the following RAG workflow:

USER QUESTION
      ↓
     TONY
      ↓
    FRIDAY
      ↓
QUERY ANALYSIS
      ↓
LOCAL QUERY EMBEDDING
      ↓
TURBOVEC VECTOR SEARCH
      ↓
RELEVANT CHUNKS
      ↓
METADATA / DOCUMENT LOOKUP
      ↓
OPTIONAL LOCAL RERANKER
      ↓
EVIDENCE SELECTION
      ↓
LOCAL LLM
      ↓
ANSWER + CITATIONS

FRIDAY must not simply send the user's question to the LLM and pretend that constitutes RAG.

The system must actually retrieve evidence from the local knowledge base.

14. Retrieval Strategy

Implement configurable:

Top-K retrieval
Similarity threshold
Metadata filtering
Optional reranking
Maximum context size
Duplicate/chunk deduplication
Document-level diversity

Example:

Question
   ↓
Embedding
   ↓
Turbovec
   ↓
Top 20 chunks
   ↓
Metadata filtering
   ↓
Local reranker
   ↓
Top 5 evidence chunks
   ↓
LLM

The exact values should be configurable rather than hard-coded.

15. Evidence-Grounded Generation

The local LLM must receive the retrieved evidence as context.

Example:

SYSTEM
 ↓
You are FRIDAY.
Answer only using the supplied evidence when the question
requires organizational knowledge.

RETRIEVED EVIDENCE
 ↓
Chunk 1
Chunk 2
Chunk 3
 ↓
USER QUESTION
 ↓
LOCAL LLM
 ↓
ANSWER

If sufficient evidence cannot be found, FRIDAY should explicitly state that the local knowledge base does not contain enough evidence.

It must not invent an answer to fill the gap.

16. Citations

Every knowledge-grounded answer should expose source information.

Minimum citation information:

Document
Page
Section
Evidence

Example:

According to the maintenance procedure, the pump should
be inspected for seal leakage before operation.

Source:
Maintenance Manual
Page 17
Section: Pump Maintenance

Citations must correspond to actual retrieved chunks.

Never fabricate document names, pages, sections, or evidence.

If page or section information is unavailable, display only the metadata that actually exists.

17. Evidence Viewer

The UI should allow the user to inspect the evidence used to generate an answer.

Example:

FRIDAY RESPONSE

Recommended inspection procedure:
...

Sources
────────────────────────
📄 Maintenance Manual
   Page 17
   Pump Maintenance

📄 Equipment SOP
   Page 42
   Inspection Procedure

Clicking an evidence item should display the relevant extracted content and, where possible, the original document/page.

This makes the system auditable rather than relying on the timeless human tradition of “trust me bro.”

18. Knowledge Workspace

Create a dedicated Knowledge Workspace.

Functions:

Upload
Upload document
      ↓
Queue processing
Processing

Show:

Uploaded
 ↓
Parsing
 ↓
OCR
 ↓
Chunking
 ↓
Embedding
 ↓
Indexing
 ↓
Ready
Search

Allow users to search the organizational knowledge base.

Browse

Allow users to browse:

Documents
Folders / Categories
Document Types
Processing Status
Versions
Delete

Deleting a document must remove:

Document metadata
Extracted content
Chunks
Vector entries
Associated index records
Re-index

Allow a document to be reprocessed when:

The document changes
The embedding model changes
Chunking configuration changes
The vector index changes
19. Versioning

Support document versions where practical.

Example:

Maintenance_Manual.pdf

v1
v2
v3 ← Current

The system should avoid mixing obsolete and current versions during retrieval unless explicitly requested.

20. Processing Queue

Document processing should be asynchronous.

Example:

UPLOAD
  ↓
JOB QUEUE
  ↓
PARSER
  ↓
OCR / VISION
  ↓
CHUNKER
  ↓
EMBEDDER
  ↓
TURBOVEC
  ↓
READY

The UI should show real processing status.

Errors should be visible and recoverable.

21. Local Storage Architecture

Use separate layers:

                    KNOWLEDGE SYSTEM
                          │
          ┌───────────────┴───────────────┐
          ↓                               ↓
   DOCUMENT STORAGE                 METADATA STORE
          │                               │
 Original Files                    Document Metadata
 Extracted Text                    Chunk Metadata
 OCR Output                        Versions
 Images                             Permissions
          │                               │
          └───────────────┬───────────────┘
                          ↓
                    TURBOVEC INDEX
                          ↓
                    Vector Search

Everything must be stored locally.

22. Security Requirements

This phase handles potentially confidential organizational information.

Therefore:

No cloud OCR
No cloud embeddings
No external vector database
No external document processing
No telemetry containing document data
No external LLM calls
No external storage
No automatic uploads

All processing must remain inside the sovereign environment.

23. Audit Logging

Log important knowledge-base operations:

Document uploaded
Document processed
OCR executed
Embedding generated
Document indexed
Search performed
Chunks retrieved
Document deleted
Document re-indexed

Do not log sensitive document contents unnecessarily.

Prefer:

document_id
timestamp
operation
user/session
status

rather than storing entire confidential documents in logs.

24. Model Router Integration

FRIDAY should use the Phase 2 Tony Stark model router.

The router should be able to select an appropriate local model based on:

Task
 ↓
Text / Vision requirement
 ↓
Reasoning requirement
 ↓
Context size
 ↓
Available GPU resources
 ↓
Model capability
 ↓
Selected local model

Examples:

Text RAG
→ Local text/reasoning model

Scanned document
→ Local vision/OCR pipeline + text model

Engineering image
→ Local vision-capable model

Complex technical reasoning
→ Stronger local reasoning model

The selected model should be visible in the UI.

25. Failure Handling

Handle cases where:

No document exists
No relevant evidence found.
OCR fails
OCR processing failed.
Document cannot currently be searched.
Retrieval confidence is low
Insufficient evidence found in the knowledge base.
Vector index fails

Automatically report the processing/indexing failure and preserve enough state for re-indexing.

Document is deleted

Remove its associated vectors and metadata.

26. Acceptance Test — Standard RAG

Upload sample industrial documentation.

Ask:

According to the maintenance documentation, what is the recommended inspection procedure?

FRIDAY must:

Receive the question.
Search the local knowledge base.
Generate a local query embedding.
Search Turbovec.
Retrieve relevant chunks.
Retrieve associated document metadata.
Optionally rerank the retrieved evidence locally.
Send the evidence to a local LLM.
Generate an answer.
Display document/page/section references.
Allow the user to inspect the evidence.
Avoid fabricating unsupported information.
27. Acceptance Test — Scanned PDF

Upload a scanned maintenance document.

The system must:

Scanned PDF
 ↓
Automatic Detection
 ↓
Local OCR
 ↓
Extracted Text
 ↓
Chunking
 ↓
Local Embeddings
 ↓
Turbovec
 ↓
FRIDAY
 ↓
Answer + Evidence

Ask a question whose answer exists inside the scanned document.

Verify that FRIDAY can retrieve and cite the OCR-derived content.

28. Acceptance Test — Multimodal Document

Upload a document containing:

Text
Tables
Images or diagrams

Verify that the system can process the supported elements locally and maintain their relationship with the source document.

29. Acceptance Test — No Evidence

Ask FRIDAY a question that is not answered by the uploaded knowledge base.

Expected behavior:

FRIDAY

I could not find sufficient evidence in the local
knowledge base to answer this reliably.

It must not hallucinate a document citation.

30. Acceptance Test — Re-indexing

Upload a document.

Verify:

Upload
 ↓
Process
 ↓
Embed
 ↓
Turbovec Index

Modify/re-upload the document.

Verify that the system can:

Detect New Version
 ↓
Reprocess
 ↓
Generate New Embeddings
 ↓
Update Turbovec
 ↓
Update Metadata

Old vectors must not incorrectly override the current document version.

31. Phase 3 Final Architecture

The completed Phase 3 architecture should look like:

                         USER
                           │
                           ↓
                    TONY STARK
                    ORCHESTRATOR
                           │
                           ↓
                        FRIDAY
                           │
                    QUERY ANALYSIS
                           │
                           ↓
                 LOCAL EMBEDDING MODEL
                           │
                           ↓
                    ┌────────────┐
                    │  TURBOVEC  │
                    │ VECTOR IDX │
                    └─────┬──────┘
                          │
                    TOP-K CHUNKS
                          │
                          ↓
                 METADATA / DOC STORE
                          │
                          ↓
                  LOCAL RERANKER
                          │
                          ↓
                  EVIDENCE SELECTION
                          │
                          ↓
                     LOCAL LLM
                          │
                          ↓
                ANSWER + CITATIONS
                          │
                          ↓
                   EVIDENCE VIEWER

Document ingestion operates alongside it:

PDF / DOCX / XLSX / PPTX / CSV / TXT / IMAGE
                         │
                         ↓
                    INGESTION
                         │
                         ↓
              PARSER / OCR / VISION
                         │
                         ↓
                  TEXT + STRUCTURE
                         │
                         ↓
                     CHUNKING
                         │
                         ↓
                LOCAL EMBEDDINGS
                         │
                         ↓
                     TURBOVEC
                         │
                         ↓
                  KNOWLEDGE BASE
Phase 3 Definition of Done

Phase 3 is complete when the system can:

Ingest supported industrial documents locally.
Detect and process scanned PDFs.
Perform local OCR.
Process supported visual content with local vision models.
Generate embeddings using local models.
Index embeddings using Turbovec.
Store document/chunk metadata separately.
Retrieve relevant evidence using vector search.
Apply metadata filtering.
Optionally rerank results locally.
Give FRIDAY access to retrieved organizational knowledge.
Generate evidence-grounded answers using local LLMs.
Display real document/page/section citations.
Allow users to inspect retrieved evidence.
Upload, browse, search, delete, and re-index documents.
Handle document versions.
Record knowledge-base operations in the audit log.
Operate without external APIs or cloud services.

Primary architectural rule:

Turbovec is the vector retrieval engine, not the entire RAG system.

The complete Phase 3 stack should therefore be:

LOCAL DOCUMENTS
      +
LOCAL PARSERS / OCR / VISION
      +
LOCAL EMBEDDING MODEL
      +
TURBOVEC
      +
LOCAL METADATA / DOCUMENT STORE
      +
LOCAL RERANKER
      +
LOCAL LLM
      =
SOVEREIGN LOCAL RAG