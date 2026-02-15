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

def _push():
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

def log_request(query_id, query, answer, latency, tokens_input, tokens_output,
                chunks_retrieved, error=None):
    entry = {
        "id": query_id,
        "timestamp": time.time(),
        "query": query,
        "answer": answer,
        "latency": latency,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "chunks_retrieved": chunks_retrieved,
        "error": str(error) if error else None,
        "feedback": None,
    }
    with _lock:
        with open(LOGS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    _push()

def record_feedback(query_id, is_relevant):
    with _lock:
        # Read all entries, update the matching one
        entries = []
        if LOGS_FILE.exists():
            with open(LOGS_FILE, "r") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue

        for entry in entries:
            if entry.get("id") == query_id:
                entry["feedback"] = is_relevant
                break

        with open(LOGS_FILE, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
    _push()
