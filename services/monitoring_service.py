import time
import json
import os
import threading
from pathlib import Path
from huggingface_hub import HfApi

HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "aniketp2009gmail/omnidoc-qa-logs"
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOGS_FILE = LOGS_DIR / "rag_requests.jsonl"

_lock = threading.Lock()
_api = HfApi(token=HF_TOKEN)

def _ensure_repo():
    try:
        _api.create_repo(repo_id=REPO_ID, repo_type="dataset", private=True, exist_ok=True)
    except Exception:
        pass

_ensure_repo()

def _make_entry(entry_type, query=None, latency=None, tokens_input=None,
                tokens_output=None, chunks_retrieved=None, error=None,
                is_relevant=None):
    return {
        "timestamp": time.time(),
        "type": entry_type,
        "query": query,
        "latency": latency,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "chunks_retrieved": chunks_retrieved,
        "error": error,
        "is_relevant": is_relevant,
    }

def _append_and_push(entry):
    with _lock:
        with open(LOGS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    try:
        _api.upload_file(
            path_or_fileobj=str(LOGS_FILE),
            path_in_repo="rag_requests.jsonl",
            repo_id=REPO_ID,
            repo_type="dataset",
        )
    except Exception:
        _ensure_repo()
        try:
            _api.upload_file(
                path_or_fileobj=str(LOGS_FILE),
                path_in_repo="rag_requests.jsonl",
                repo_id=REPO_ID,
                repo_type="dataset",
            )
        except Exception as e:
            print(f"HF upload error: {e}")

def log_request(query, latency, tokens_input, tokens_output, chunks_retrieved, error=None):
    entry = _make_entry(
        "request",
        query=query,
        latency=latency,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        chunks_retrieved=chunks_retrieved,
        error=str(error) if error else None,
    )
    _append_and_push(entry)

def record_feedback(is_relevant):
    entry = _make_entry("feedback", is_relevant=is_relevant)
    _append_and_push(entry)
