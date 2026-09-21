import json
import logging
from enum import Enum
from pathlib import Path
from uuid import UUID

import pytest

from src.infrastructure.logging.config import (
    EnumEncoder,
    JSONFormatter,
    RequestIDFilter,
    RequestIDScope,
    _collect_extra,
    get_request_id,
    setup_logging,
)


class SampleStatus(Enum):
    ACTIVE = "active"


@pytest.mark.unit
class TestEnumEncoder:
    def test_enum_encoder_serializes_enum_value(self) -> None:
        encoded = json.dumps({"status": SampleStatus.ACTIVE}, cls=EnumEncoder)

        assert json.loads(encoded) == {"status": "active"}


@pytest.mark.unit
class TestRequestIDFilter:
    def test_request_id_filter_default_dash_outside_scope(self) -> None:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        assert RequestIDFilter().filter(record) is True
        assert record.request_id == "-"

    def test_request_id_filter_uses_scoped_id(self) -> None:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        with RequestIDScope("req-123"):
            RequestIDFilter().filter(record)

        assert record.request_id == "req-123"


@pytest.mark.unit
class TestRequestIDScope:
    def test_request_id_scope_enter_returns_id(self) -> None:
        with RequestIDScope("fixed-id") as request_id:
            assert request_id == "fixed-id"
            assert get_request_id() == "fixed-id"

    def test_request_id_scope_exit_resets_context(self) -> None:
        with RequestIDScope("temporary"):
            pass

        assert get_request_id() is None

    def test_request_id_scope_generates_uuid_when_not_provided(self) -> None:
        with RequestIDScope() as request_id:
            UUID(request_id)

    def test_get_request_id_none_outside_scope(self) -> None:
        assert get_request_id() is None


@pytest.mark.unit
class TestJSONFormatter:
    def test_json_formatter_includes_required_keys(self) -> None:
        formatter = JSONFormatter("auth-service", "0.1.0")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.request_id = "rid-1"

        payload = json.loads(formatter.format(record))

        assert payload["level"] == "INFO"
        assert payload["message"] == "hello"
        assert payload["service"] == "auth-service"
        assert payload["version"] == "0.1.0"
        assert payload["request_id"] == "rid-1"
        assert "timestamp" in payload

    def test_json_formatter_includes_extra_fields(self) -> None:
        formatter = JSONFormatter("auth-service", "0.1.0")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.email = "user@example.com"

        payload = json.loads(formatter.format(record))

        assert payload["extra"]["email"] == "user@example.com"

    def test_json_formatter_includes_exception_on_exc_info(self) -> None:
        formatter = JSONFormatter("auth-service", "0.1.0")
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname=__file__,
                lineno=10,
                msg="failed",
                args=(),
                exc_info=sys.exc_info(),
            )

        payload = json.loads(formatter.format(record))

        assert "exception" in payload
        assert "ValueError: boom" in payload["exception"]

    def test_collect_extra_stringifies_non_serializable(self) -> None:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.payload = object()

        extra = _collect_extra(record)

        assert isinstance(extra["payload"], str)


@pytest.mark.unit
class TestSetupLogging:
    def test_setup_logging_console_only_without_path(self) -> None:
        setup_logging(
            level="INFO",
            service_name="auth-service",
            service_version="0.1.0",
        )

        root = logging.getLogger()
        handler_types = {type(handler).__name__ for handler in root.handlers}

        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" not in handler_types

    def test_setup_logging_adds_file_handler_with_path(self, tmp_path: Path) -> None:
        log_path = tmp_path / "app.log"
        setup_logging(
            level="INFO",
            service_name="auth-service",
            service_version="0.1.0",
            log_path=str(log_path),
        )

        root = logging.getLogger()
        handler_types = {type(handler).__name__ for handler in root.handlers}

        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" in handler_types
