from app.queue import redis_connection
from rq import Queue


dead_letter_queue = Queue(
    "dead-letter",
    connection=redis_connection,
)
