from redis import Redis
from rq import Queue

redis_connection = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

queue = Queue(
    "default",
    connection=redis_connection,
)
