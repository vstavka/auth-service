import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import grpc
from grpc import aio, StatusCode

from src.infrastructure.logging.config import RequestIDScope

logger = logging.getLogger(__name__)

_REQUEST_ID_METADATA_KEYS = ("x-request-id", "request-id")
_Handler = Any


class LoggingInterceptor(aio.ServerInterceptor):
    """Логирует unary gRPC-вызовы: method, status, duration."""

    def __init__(self, *, slow_request_threshold_seconds: float = 3.0) -> None:
        self._slow_threshold = slow_request_threshold_seconds

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Awaitable[_Handler | None]],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> _Handler | None:
        handler = await continuation(handler_call_details)
        if handler is None:
            return None

        method = handler_call_details.method
        if handler.unary_unary is not None:
            return self._wrap_unary_unary(handler, method)
        return handler

    def _wrap_unary_unary(self, handler: _Handler, method: str) -> _Handler:
        original = handler.unary_unary

        async def unary_unary(request: Any, context: aio.ServicerContext) -> Any:
            start = time.perf_counter()
            peer = context.peer()
            request_id = _metadata_value(context, *_REQUEST_ID_METADATA_KEYS)

            with RequestIDScope(request_id):
                logger.debug(
                    "Incoming gRPC request",
                    extra={"rpc": method, "peer": peer},
                )
                try:
                    response = await original(request, context)
                except aio.AbortError:
                    duration_ms = round((time.perf_counter() - start) * 1000, 2)
                    code = context.code() or StatusCode.UNKNOWN
                    logger.info(
                        "gRPC response",
                        extra={
                            "rpc": method,
                            "peer": peer,
                            "status": code.name,
                            "duration_ms": duration_ms,
                        },
                    )
                    raise
                except Exception:
                    duration_ms = round((time.perf_counter() - start) * 1000, 2)
                    logger.exception(
                        "gRPC request failed",
                        extra={
                            "rpc": method,
                            "peer": peer,
                            "status": StatusCode.UNKNOWN.name,
                            "duration_ms": duration_ms,
                        },
                    )
                    raise

                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                code = context.code() or StatusCode.OK
                logger.info(
                    "gRPC response",
                    extra={
                        "rpc": method,
                        "peer": peer,
                        "status": code.name,
                        "duration_ms": duration_ms,
                    },
                )
                if duration_ms > self._slow_threshold * 1000:
                    logger.warning(
                        "Slow gRPC request",
                        extra={
                            "rpc": method,
                            "peer": peer,
                            "status": code.name,
                            "duration_ms": duration_ms,
                        },
                    )
                return response

        return grpc.unary_unary_rpc_method_handler(
            unary_unary,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


def _metadata_value(context: aio.ServicerContext, *keys: str) -> str | None:
    wanted = {key.lower() for key in keys}
    for meta_key, meta_value in context.invocation_metadata():
        if meta_key.lower() not in wanted:
            continue
        if isinstance(meta_value, bytes):
            return meta_value.decode("utf-8")
        return str(meta_value)
    return None
