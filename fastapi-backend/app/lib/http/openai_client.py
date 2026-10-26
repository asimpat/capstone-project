import os
import time

import httpx
from dotenv import load_dotenv
from app.lib.http.retry import with_retry
from app.utils.logger import logger

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def log_request(request: httpx.Request):
    request.extensions["start_time"] = time.perf_counter()

    logger.info(
        "Ollama request | method=%s url=%s",
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
        "Ollama response | status=%s url=%s duration_ms=%.2f",
        response.status_code,
        response.request.url,
        duration,
    )

    check_rate_limit(response)


ollama_client = httpx.Client(
    base_url=OLLAMA_BASE_URL,
    timeout=120.0,
    headers={
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
        response = ollama_client.post(
            path,
            json=payload,
        )

        response.raise_for_status()

        return response

    except httpx.HTTPStatusError as error:
        logger.error(
            "Ollama HTTP error | status=%s error=%s",
            error.response.status_code,
            error.response.text,
        )
        raise

    except httpx.TimeoutException as error:
        logger.error(
            "Ollama timeout | error=%s",
            error,
        )
        raise

    except httpx.RequestError as error:
        logger.exception(
            "Ollama request setup error"
        )
        raise

    except Exception:
        logger.exception(
            "Ollama request setup error"
        )
        raise


def openai_post_with_retry(path: str, payload: dict):
    return with_retry(
        lambda: openai_post(path, payload)
    )


def check_rate_limit(response: httpx.Response):
    return
