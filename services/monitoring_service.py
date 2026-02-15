import time
import json
import os
from pathlib import Path
from huggingface_hub import CommitScheduler

HF_TOKEN = os.getenv("HF_TOKEN")
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOGS_FILE = LOGS_DIR / "rag_requests.jsonl"

scheduler = CommitScheduler(
    repo_id="aniketp2009gmail/omnidoc-qa-logs",
    repo_type="dataset",
    folder_path=LOGS_DIR,
    path_in_repo=".",
    token=HF_TOKEN,
    every=2,
    private=True,
)

def log_request(query, latency, tokens_input, tokens_output, chunks_retrieved, error=None):
    entry = {
        "timestamp": time.time(),
        "type": "request",
        "query": query,
        "latency": latency,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "chunks_retrieved": chunks_retrieved,
        "error": str(error) if error else None,
    }
    with scheduler.lock:
        with open(LOGS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

def record_feedback(is_relevant):
    entry = {
        "timestamp": time.time(),
        "type": "feedback",
        "is_relevant": is_relevant,
    }
    with scheduler.lock:
        with open(LOGS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
