from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import re


# ============================================================
# HTTP METRICS
# ============================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)


# ============================================================
# DOCUMENT METRICS
# ============================================================

documents_processed = Counter(
    "docuchat_documents_processed_total",
    "Number of documents processed",
    ["status"],
)

ingestion_duration = Histogram(
    "docuchat_ingestion_duration_seconds",
    "Document ingestion duration",
    ["format"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

chunks_per_document = Histogram(
    "docuchat_chunks_per_document",
    "Number of chunks generated per document",
    buckets=[5, 10, 25, 50, 100, 250, 500],
)

embedding_cache_hit_rate = Gauge(
    "docuchat_embedding_cache_hit_rate",
    "Percentage of embedding requests served from cache",
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def normalize_path(path: str) -> str:
    """
    Normalize URL paths for metrics aggregation.
    Converts /api/v1/documents/cuid123 to /api/v1/documents/{id}
    """
    # Replace UUIDs and CUIDs with {id}
    path = re.sub(r'/[a-z0-9_-]{24,}(?=/|$)', '/{id}', path, flags=re.IGNORECASE)
    
    # Replace numeric IDs
    path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
    
    return path
