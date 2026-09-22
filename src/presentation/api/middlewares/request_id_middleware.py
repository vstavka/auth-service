import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.config import RequestIDScope

logger = logging.getLogger(__name__)

import re

_REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")


def _sanitize_request_id(value: str | None) -> str | None:
    if value and _REQUEST_ID_PATTERN.match(value):
        return value
    return None


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for setting request_id in request context."""

    async def dispatch(self, request: Request, call_next):
        incoming_id = _sanitize_request_id(request.headers.get("X-Request-ID"))

        with RequestIDScope(incoming_id) as request_id:
            request.state.request_id = request_id
            logger.debug(
                "Request ID set",
                extra={"from_header": incoming_id is not None},
            )
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
