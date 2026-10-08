from prometheus_client import Counter, Gauge, Histogram


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
