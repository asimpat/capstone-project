import time

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.utils.metrics import (
    http_requests_total,
    http_request_duration,
    normalize_path,
)


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start

        path = normalize_path(
            request.url.path
        )

        http_requests_total.labels(
            method=request.method,
            path=path,
            status_code=str(response.status_code),
        ).inc()

        http_request_duration.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        return response
