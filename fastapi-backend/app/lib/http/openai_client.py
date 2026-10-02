import os
import time

import httpx
from dotenv import load_dotenv
from app.lib.http.retry import with_retry
from app.utils.logger import logger

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not configured")


def log_request(request: httpx.Request):
    request.extensions["start_time"] = time.perf_counter()

    logger.info(
        "OpenAI request | method=%s url=%s",
        request.method,
        request.url,
    )


def log_response(response: httpx.Response):
    start_time = response.request.extensions.get("start_time")

    duration = 0

    if start_time:
        duration = int(
            (time.perf_counter() - start_time) * 1000
        )


    logger.info(
        "OpenAI response | status=%s url=%s duration_ms=%.2f",
        response.status_code,
        response.request.url,
        duration,
    )

    check_rate_limit(response)


openai_client = httpx.Client(
    base_url="https://api.openai.com/v1",
    timeout=30.0,
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "DocuChat/1.0",
    },
    event_hooks={
        "request": [log_request],
        "response": [log_response],
    },
)


def openai_post(path: str, payload: dict):
    try:
        response = openai_client.post(
            path,
            json=payload,
        )

        response.raise_for_status()

        return response

    except httpx.HTTPStatusError as error:
        logger.error(
            "OpenAI HTTP error | status=%s error=%s",
            error.response.status_code,
            error.response.text,
        )
        raise

    except httpx.TimeoutException as error:
        logger.error(
            "OpenAI timeout | error=%s",
            error,
        )
        raise

    except httpx.RequestError as error:
        logger.exception(
            "OpenAI request setup error"
        )
        raise

    except Exception as error:
        logger.exception(
            "OpenAI request setup error"
        )
        raise


def openai_post_with_retry(path: str, payload: dict):
    return with_retry(
        lambda: openai_post(path, payload)
    )


def check_rate_limit(response: httpx.Response):
    remaining = response.headers.get(
        "x-ratelimit-remaining-requests"
    )

    if remaining is None:
        return

    try:
        remaining = int(remaining)
    except ValueError:
        return

    if remaining < 50:
        logger.warning(
            "OpenAI rate limit getting low | remaining=%s",
            remaining,
        )
