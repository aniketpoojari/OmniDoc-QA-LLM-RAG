# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│  Bootstrap 5 + jQuery + DOMPurify                       │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │ Document Mgmt│  │ Chat Interface                   │ │
│  │ - PDF upload │  │ - Question input                 │ │
│  │ - URL input  │  │ - Response + inline metrics      │ │
│  │ - Doc list   │  │ - Feedback buttons (per response)│ │
│  └──────┬───────┘  └──────────────┬───────────────────┘ │
└─────────┼──────────────────────────┼────────────────────┘
          │ AJAX                     │ AJAX
┌─────────▼──────────────────────────▼────────────────────┐
│                    Flask Backend (app.py)                │
│                                                         │
│  /upload_pdf ──► PDF Extraction ──► Chunk + Embed ──┐   │
│  /process_website ► Web Extraction ► Chunk + Embed ─┤   │
│  /delete_document ──────────────────────────────────►│   │
│                                                      │   │
│                                              ┌───────▼─┐ │
│  /ask_question ──► Retrieve ──► LLM Chain ──►│ChromaDB │ │
│        │                                     └─────────┘ │
│        ▼                                                 │
│  /feedback ──► Update row by query_id                    │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────┐                                │
│  │ Monitoring Service   │                                │
│  │ Local JSONL + HfApi  │──── push ──► HF Dataset        │
│  └──────────────────────┘                                │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────┐     ┌──────────────────┐
│   Streamlit Dashboard   │────►│ HF Dataset       │
│   (dashboard.py)        │pull │ omnidoc-qa-logs   │
└─────────────────────────┘     └──────────────────┘
```

## Data Flow

### 1. Document Ingestion

```
PDF/URL → Extraction Service → Raw text + tables
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                    Raw text chunks          Table strings
                          │                       │
                          │              LLM validates table
                          │              (True/False check)
                          │                       │
                          │              LLM serializes table
                          │              to structured text
                          │                       │
                          └───────────┬───────────┘
                                      ▼
                          RecursiveCharacterTextSplitter
                          (chunk_size=500, overlap=50)
                                      │
                                      ▼
                          all-MiniLM-L6-v2 embedding
                                      │
                                      ▼
                              ChromaDB (in-memory)
                              tagged with source ID
```

**PDF extraction** uses PyMuPDF for text and Tabula for tables. Tables go through a two-step LLM process: first a classifier decides if a table is meaningful (returns True/False), then an extractor serializes it into text that can be chunked and embedded alongside the document text.

**Website extraction** uses BeautifulSoup4 with browser-like headers. It identifies the main content area (article/main tags), strips navigation, scripts, ads, and hidden elements, then extracts clean text and any HTML tables.

### 2. Query Pipeline

```
User question
      │
      ▼
Comparative query detection (regex)
      │
      ├── Standard query: k=8 chunks
      └── Comparative query: k=20 chunks, balanced across sources
                │
                ▼
        ChromaDB similarity search
                │
                ▼
        Context assembly (concatenate chunk texts)
                │
                ▼
        LLM prompt (system context + user question)
        Groq API → LLaMA 3.1 8B Instant
                │
                ▼
        Response + token usage metadata
                │
                ├──► Chat UI (response + inline metrics)
                └──► Monitoring Service (log to HF Dataset)
```

**Comparative query detection** uses regex to identify keywords like "compare", "contrast", "versus", "both", "all documents". When detected, retrieval pulls more chunks (20 vs 8) and balances them evenly across document sources so no single source dominates the context.

### 3. Feedback + Logging

```
/ask_question response
      │
      ├── query_id (UUID)
      ├── query, answer, latency, tokens, chunks
      │
      ▼
  log_request() → append JSONL → HfApi.upload_file() → HF Dataset

User clicks thumbs up/down
      │
      ├── query_id + is_relevant
      │
      ▼
  record_feedback() → find row by ID → update feedback field → re-push
```

Each query gets a UUID. The full row (question, answer, metrics, feedback) lives as a single JSONL entry. Feedback updates the existing row in place rather than appending a new entry, so every row in the dataset tells the complete story.

## Design Decisions

### Why ChromaDB in-memory (no persistence)?
This is a session-based tool — users upload documents, ask questions, then leave. Persisting vectors across sessions would require managing stale data and user isolation. In-memory keeps it simple and stateless.

### Why Groq over OpenAI/Anthropic?
Groq provides free-tier access with fast inference on open-weight models. For a portfolio project, this removes the cost barrier while demonstrating the same RAG patterns that work with any LLM provider.

### Why HF Datasets for logging instead of a database?
- Works identically locally and on HF Spaces without provisioning infrastructure
- Dataset is versioned and browsable through the HF web UI
- Streamlit dashboard can pull logs with a single `hf_hub_download()` call
- Demonstrates HF ecosystem integration (relevant for ML roles)

### Why immediate uploads instead of batching?
Traffic on a portfolio app is low. Immediate uploads ensure no data loss if the container restarts (HF Spaces containers are ephemeral). The latency overhead of one `upload_file()` call per query is acceptable at this scale.

### Why client-side session IDs instead of Flask sessions?
Flask's default cookie-based sessions failed on Hugging Face Spaces — the reverse proxy strips or doesn't forward `Set-Cookie` headers, so the session cookie was lost between requests. Users would upload a document, then get "Please upload at least one document first" when asking a question because the backend saw a new (empty) session each time.

The fix: JavaScript generates a UUID per browser tab (`crypto.randomUUID()`) and sends it as an `X-Session-Id` header with every AJAX request via `$.ajaxSetup`. The backend keys into a server-side dict using this header. This is cookie-free, proxy-safe, and gives true per-tab isolation as a bonus — two tabs in the same browser get independent sessions.

### Why two-step table processing?
Raw Tabula output often includes malformed or empty tables. The classifier step filters noise before the extractor step spends tokens serializing table content. This keeps the vector store clean and avoids polluting retrieval with garbage chunks.

## Deployment

```
GitHub (main branch)
      │
      │ push
      ▼
GitHub Actions (deploy-hf-spaces.yml)
      │
      │ git push --force
      ▼
Hugging Face Spaces (Docker SDK)
      │
      │ builds Dockerfile
      ▼
Running container (port 7860)
      │
      ├── GROQ_API_KEY (Space Secret)
      └── HF_TOKEN (Space Secret)
```

The Dockerfile uses `python:3.11-slim`, installs `default-jre-headless` (required by Tabula for table extraction), and runs as a non-root user with UID 1000 (HF Spaces requirement).
