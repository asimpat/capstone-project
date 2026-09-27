import pybreaker

from app.lib.http.retry import with_retry
from app.lib.http.openai_client import openai_post


openai_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
)


def call_openai(path: str, payload: dict):
    return openai_breaker.call(
        lambda: with_retry(
            lambda: openai_post(path, payload)
        )
    )


@openai_breaker.half_open
def on_half_open():
    print("⚠️ OpenAI circuit breaker HALF-OPEN")


@openai_breaker.closed
def on_closed():
    print("✅ OpenAI circuit breaker CLOSED")


@openai_breaker.opened
def on_opened():
    print("⚠️ OpenAI circuit breaker OPENED")
