from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Pages that render HTML and load assets from the jsDelivr CDN
DOCS_PATHS = {"/docs", "/redoc", "/docs/oauth2-redirect"}

# Swagger UI: CDN script + CSS, inline bootstrap script, favicon from fastapi.tiangolo.com.
# ReDoc: CDN script, Google Fonts, blob: web worker.
DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "worker-src blob:; "
    "connect-src 'self'"
)

# API-only responses (JSON)
API_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "connect-src 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-DNS-Prefetch-Control"] = "off"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        if request.url.path in DOCS_PATHS:
            response.headers["Content-Security-Policy"] = DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = API_CSP

        return response
