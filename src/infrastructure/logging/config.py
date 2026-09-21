import json
import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, UTC
from enum import Enum
from typing import Any

import colorlog

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)

_NO_REQUEST_ID = "-"

_RESERVED_RECORD_KEYS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "exc_info", "exc_text",
    "stack_info", "request_id", "message", "asctime",
})


class EnumEncoder(json.JSONEncoder):
    """Converts Enum to its value for JSON serialization."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class RequestIDFilter(logging.Filter):
    """Attaches current request_id (or placeholder) to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get() or _NO_REQUEST_ID
        return True


def _collect_extra(record: logging.LogRecord) -> dict[str, Any]:
    """Собирает пользовательские extra-поля, не входящие в стандартные атрибуты LogRecord."""
    extra: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key in _RESERVED_RECORD_KEYS:
            continue
        try:
            json.dumps(value, cls=EnumEncoder)
            extra[key] = value
        except (TypeError, ValueError):
            extra[key] = str(value)
    return extra


class JSONFormatter(logging.Formatter):
    """Structured JSON logger with a stable schema across all records."""

    def __init__(self, service_name: str, service_version: str):
        super().__init__()
        self._service_name = service_name
        self._service_version = service_version

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self._service_name,
            "version": self._service_version,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", _NO_REQUEST_ID),
        }

        extra = _collect_extra(record)
        if extra:
            payload["extra"] = extra

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, cls=EnumEncoder)


class ColoredConsoleFormatter(colorlog.ColoredFormatter):
    """Colored console output with request_id and extra fields inline."""

    _GRAY = "\033[90m"
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        extra = _collect_extra(record)
        if extra:
            extra_text = " | ".join(f"{self._GRAY}{k}{self._RESET}={v}" for k, v in extra.items())
            message = f"{message} | {extra_text}"

        return message


class RequestIDScope:
    """Context manager для установки request_id на время блока (например, обработки запроса)."""

    def __init__(self, request_id: str | None = None):
        self._request_id = request_id or str(uuid.uuid4())
        self._token = None

    def __enter__(self) -> str:
        self._token = request_id_context.set(self._request_id)
        return self._request_id

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        request_id_context.reset(self._token)


def get_request_id() -> str | None:
    """Returns the current request_id or None if not set."""
    return request_id_context.get()


def setup_logging(
    *,
    level: str,
    service_name: str,
    service_version: str,
    log_path: str | None = None,
) -> None:
    """
    Configure logging:
    - colored console output with request_id and extra fields;
    - JSON log to file (if log_path is provided);
    - RequestIDFilter attached to every handler.
    """
    use_color = sys.stdout.isatty()
    console_fmt = (
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s "
        f"{ColoredConsoleFormatter._GRAY}[%(request_id)s]{ColoredConsoleFormatter._RESET} "
        "%(message)s"
        if use_color
        else "%(asctime)s %(levelname)-8s [%(request_id)s] %(message)s"
    )

    formatters = {
        "json": {
            "()": JSONFormatter,
            "service_name": service_name,
            "service_version": service_version,
        },
        "console": {
            "()": ColoredConsoleFormatter,
            "format": console_fmt,
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            "reset": True,
        },
    }

    handlers: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "console",
            "filters": ["request_id"],
            "stream": sys.stdout,
        },
    }

    if log_path:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "json",
            "filters": ["request_id"],
            "filename": log_path,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        }

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "filters": {"request_id": {"()": RequestIDFilter}},
        "handlers": handlers,
        "loggers": {
            "": {
                "level": level,
                "handlers": list(handlers.keys()),
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
    logging.getLogger("app.startup").info(
        "Logging configured",
        extra={"log_level": level, "log_path": log_path or "stdout"},
    )