# Phase 3 — Industrial Document AI & Local RAG

## Objective

Create the local multimodal document and organizational knowledge layer.

## Pipeline

```text
FILE
 ↓
INGESTION
 ↓
PARSER / OCR
 ↓
CHUNKING
 ↓
LOCAL EMBEDDINGS
 ↓
VECTOR DATABASE
 ↓
FRIDAY
 ↓
EVIDENCE-GROUNDED RESPONSE
```

## Document Ingestion

Support:
- PDF
- Scanned PDF
- DOCX
- XLSX
- PPTX
- TXT
- CSV
- Images

Extract text and metadata.

## OCR

Use local OCR only.

Detect scanned documents automatically.

## Vision

Support local vision-capable models for:
- Images
- Scanned documents
- Tables
- Diagrams
- Engineering drawings where supported

## Embeddings

Use local embedding models.

No external embedding API.

## Vector Database

Store:
- Chunk
- Document ID
- Page
- Section
- Source
- Timestamp
- Embedding

## RAG

```text
Question
 ↓
FRIDAY
 ↓
Query Embedding
 ↓
Vector Search
 ↓
Relevant Chunks
 ↓
Local Model
 ↓
Answer + Evidence
```

## Citations

Expose:
- Document
- Page
- Section
- Relevant evidence

Never fabricate citations.

## Knowledge Workspace

Support:
- Upload
- Processing status
- Search
- Browse
- Delete
- Re-index

## Acceptance Test

Upload sample industrial documentation.

Ask:

> According to the maintenance documentation, what is the recommended inspection procedure?

FRIDAY must:
1. Search local KB
2. Retrieve relevant chunks
3. Answer with local model
4. Show evidence/page references

Also test scanned PDFs through local OCR.
