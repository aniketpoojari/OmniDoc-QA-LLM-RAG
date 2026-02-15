import time
import json
import os
from prometheus_client import Counter, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST

# Metrics
REQUEST_COUNT = Counter('rag_request_count', 'Total RAG requests', ['endpoint', 'status'])
REQUEST_LATENCY = Histogram('rag_request_latency_seconds', 'Request latency', ['endpoint'], buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0])
TOKEN_USAGE = Counter('rag_token_usage_total', 'Token usage', ['type']) # type: input, output
RETRIEVAL_LATENCY = Histogram('rag_retrieval_latency_seconds', 'Retrieval latency')
CHUNKS_RETRIEVED = Histogram('rag_chunks_retrieved_count', 'Number of chunks retrieved', buckets=[1, 2, 3, 5, 10, 20])
EMBEDDING_LATENCY = Histogram('rag_embedding_latency_seconds', 'Embedding latency')
ERROR_RATE = Counter('rag_error_rate_total', 'Total errors', ['error_type'])

# Retrieval Quality Tracking
RETRIEVAL_FEEDBACK = Counter('rag_retrieval_feedback_total', 'Retrieval feedback', ['is_relevant'])

LOG_FILE = 'logs/rag_requests.jsonl'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_request(query, latency, tokens_input, tokens_output, chunks_retrieved, error=None):
    log_entry = {
        'timestamp': time.time(),
        'query': query,
        'latency': latency,
        'tokens_input': tokens_input,
        'tokens_output': tokens_output,
        'chunks_retrieved': chunks_retrieved,
        'error': str(error) if error else None
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def get_metrics_data():
    return generate_latest(), CONTENT_TYPE_LATEST

def get_stats_summary():
    # Simple summary of stats
    total_requests = sum(c._value.get() for c in REQUEST_COUNT._metrics.values()) if hasattr(REQUEST_COUNT, '_metrics') else 0
    
    # Calculate precision
    relevant_count = RETRIEVAL_FEEDBACK.labels(is_relevant='True')._value.get()
    irrelevant_count = RETRIEVAL_FEEDBACK.labels(is_relevant='False')._value.get()
    total_feedback = relevant_count + irrelevant_count
    precision = (relevant_count / total_feedback) if total_feedback > 0 else 0

    return {
        "status": "healthy",
        "total_requests": total_requests,
        "retrieval_precision": precision,
        "total_feedback": total_feedback,
        "timestamp": time.time()
    }

def record_feedback(is_relevant):
    RETRIEVAL_FEEDBACK.labels(is_relevant=str(is_relevant)).inc()
