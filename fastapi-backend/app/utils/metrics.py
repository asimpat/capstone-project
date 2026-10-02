from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from prometheus_client import CollectorRegistry


# Total HTTP requests
http_requests_total = Counter(
    "docuchat_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)


# HTTP request duration
http_request_duration = Histogram(
    "docuchat_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1,
        2.5,
        5,
        10,
    ],
)


# Documents processed
documents_processed = Counter(
    "docuchat_documents_processed_total",
    "Documents processed by the queue worker",
    ["status"],
)


# Active queue jobs
active_queue_jobs = Gauge(
    "docuchat_active_queue_jobs",
    "Currently active queue jobs",
    ["queue"],
)


# Cache operations
cache_operations = Counter(
    "docuchat_cache_operations_total",
    "Cache operations",
    ["operation", "result"],
)


def normalize_path(path: str) -> str:
    """
    Prevent metric cardinality explosion.
    """

    import re

    path = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{4}-"
        r"[0-9a-f]{12}",
        "/:id",
        path,
        flags=re.IGNORECASE,
    )

    path = re.sub(
        r"/\d+",
        "/:num",
        path,
    )

    return path
