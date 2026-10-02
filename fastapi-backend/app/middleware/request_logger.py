import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.utils.logger import logger


class RequestLoggerMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        correlation_id = request.headers.get(
            "X-Correlation-Id"
        ) or str(uuid.uuid4())

        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()

        logger.info(
            "Request received | correlation_id=%s method=%s path=%s",
            correlation_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)

            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            response.headers[
                "X-Correlation-Id"
            ] = correlation_id

            if response.status_code >= 500:
                logger.error(
                    "Request failed | correlation_id=%s "
                    "status=%s duration_ms=%.2f",
                    correlation_id,
                    response.status_code,
                    duration_ms,
                )

            elif response.status_code >= 400:
                logger.warning(
                    "Request client error | correlation_id=%s "
                    "status=%s duration_ms=%.2f",
                    correlation_id,
                    response.status_code,
                    duration_ms,
                )

            else:
                logger.info(
                    "Request completed | correlation_id=%s "
                    "status=%s duration_ms=%.2f",
                    correlation_id,
                    response.status_code,
                    duration_ms,
                )

            return response

        except Exception:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.exception(
                "Request crashed | correlation_id=%s "
                "duration_ms=%.2f",
                correlation_id,
                duration_ms,
            )

            raise
