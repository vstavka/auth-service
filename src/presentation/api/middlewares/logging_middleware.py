import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_SLOW_REQUEST_THRESHOLD_SECONDS = 3.0
_SENSITIVE_QUERY_KEYS = {"password", "token", "secret", "access_token", "refresh_token"}


def _redact_query_params(query_params) -> str | None:
    if not query_params:
        return None
    redacted = {
        k: ("***" if k.lower() in _SENSITIVE_QUERY_KEYS else v)
        for k, v in query_params.items()
    }
    return str(redacted)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        logger.debug(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": _redact_query_params(request.query_params),
                "client": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start_time
            logger.exception(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
            raise

        duration = time.perf_counter() - start_time
        logger.info(
            "Response sent",
            extra={
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "method": request.method,
                "path": request.url.path,
            },
        )

        if duration > _SLOW_REQUEST_THRESHOLD_SECONDS:
            logger.warning(
                "Slow request",
                extra={
                    "duration_ms": round(duration * 1000, 2),
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                },
            )

        return response