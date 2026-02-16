---
title: OmniDoc QA
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# OmniDoc QA — Multi-Modal RAG System

A production-style RAG (Retrieval-Augmented Generation) application that lets users upload PDFs or websites, then ask natural-language questions over the ingested content. Built with Flask, LangChain, ChromaDB, and Groq.

**[Try it on Hugging Face Spaces](https://huggingface.co/spaces/aniketp2009gmail/OmniDoc-QA-LLM-RAG)**

## Features

- **Multi-format ingestion** — Upload PDFs or paste a website URL; text, tables, and structure are extracted automatically
- **RAG pipeline** — Documents are chunked, embedded with `all-MiniLM-L6-v2`, stored in ChromaDB, and retrieved at query time
- **Comparative queries** — Detects cross-document questions and balances retrieval across sources
- **Inline metrics** — Each response shows latency, chunks retrieved, and token usage
- **Feedback loop** — Thumbs up/down per response, stored in a Hugging Face Dataset for analysis
- **Monitoring dashboard** — Streamlit dashboard pulls logs from HF Dataset to visualize latency trends, token usage, and retrieval quality

## Quickstart

```bash
# Clone and install
git clone https://github.com/aniketpoojari/OmniDoc-QA-LLM-RAG.git
cd OmniDoc-QA-LLM-RAG
pip install -r requirements.txt

# Set API keys
echo "GROQ_API_KEY=your_key_here" >> .env
echo "HF_TOKEN=your_hf_write_token" >> .env

# Run
python app.py
# Open http://localhost:7860
```

### Monitoring Dashboard

```bash
streamlit run dashboard.py
```

Pulls logs from the HF Dataset and displays latency trends, token costs, retrieval quality, and query history.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask |
| LLM | Groq API (LLaMA 3.1 8B Instant) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB |
| Orchestration | LangChain |
| PDF extraction | PyMuPDF + Tabula |
| Web extraction | BeautifulSoup4 |
| Frontend | Bootstrap 5, jQuery, DOMPurify |
| Logging | Hugging Face Datasets (via `HfApi`) |
| Deployment | Docker on Hugging Face Spaces |
| CI/CD | GitHub Actions |

## Project Structure

```
├── app.py                          # Flask routes and main entry point
├── models/
│   └── vector_store.py             # ChromaDB wrapper (chunk, embed, store)
├── services/
│   ├── llm_service.py              # Groq LLM integration and RAG chain
│   ├── pdf_extraction_service.py   # PDF text + table extraction
│   ├── website_extraction_service.py # Web scraping and content extraction
│   └── monitoring_service.py       # HF Dataset logging and feedback
├── templates/
│   └── index.html                  # Main UI template
├── static/
│   ├── script.js                   # Frontend logic (AJAX, chat, feedback)
│   └── style.css                   # Custom styles
├── dashboard.py                    # Streamlit monitoring dashboard
├── Dockerfile                      # HF Spaces deployment
├── .github/workflows/
│   └── deploy-hf-spaces.yml        # CI/CD: GitHub → HF Spaces
└── requirements.txt
```

See [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for architecture details and design decisions.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM inference |
| `HF_TOKEN` | Yes | HuggingFace write token for logging and deployment |
| `PORT` | No | Server port (default: 7860) |
