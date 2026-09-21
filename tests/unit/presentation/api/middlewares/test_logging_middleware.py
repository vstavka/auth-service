from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import QueryParams

from src.presentation.api.middlewares.logging_middleware import (
    LoggingMiddleware,
    _redact_query_params,
)


@pytest.mark.unit
class TestRedactQueryParams:
    def test_redact_query_params_masks_sensitive_keys(self) -> None:
        params = QueryParams(
            "password=secret&token=t&secret=s&access_token=a&refresh_token=r&ok=1"
        )

        redacted = _redact_query_params(params)

        assert redacted is not None
        assert "'password': '***'" in redacted
        assert "'token': '***'" in redacted
        assert "'secret': '***'" in redacted
        assert "'access_token': '***'" in redacted
        assert "'refresh_token': '***'" in redacted
        assert "'ok': '1'" in redacted

    def test_redact_query_params_case_insensitive(self) -> None:
        params = QueryParams("PASSWORD=secret&Token=t")

        redacted = _redact_query_params(params)

        assert "'PASSWORD': '***'" in redacted
        assert "'Token': '***'" in redacted

    def test_redact_query_params_empty_returns_none(self) -> None:
        assert _redact_query_params(QueryParams("")) is None


def _build_app(*, raise_error: bool = False) -> FastAPI:
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/ok")
    async def ok() -> dict:
        return {"status": "ok"}

    @app.get("/fail")
    async def fail() -> dict:
        raise RuntimeError("boom")

    return app


@pytest.mark.unit
class TestLoggingMiddleware:
    def test_logs_incoming_request_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        client = TestClient(_build_app())

        with caplog.at_level("DEBUG", logger="src.presentation.api.middlewares.logging_middleware"):
            response = client.get("/ok")

        assert response.status_code == 200
        assert any(record.message == "Incoming request" for record in caplog.records)

    def test_logs_response_sent_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        client = TestClient(_build_app())

        with caplog.at_level("INFO", logger="src.presentation.api.middlewares.logging_middleware"):
            response = client.get("/ok")

        assert response.status_code == 200
        assert any(record.message == "Response sent" for record in caplog.records)

    def test_logs_warning_on_slow_request(self, caplog: pytest.LogCaptureFixture) -> None:
        client = TestClient(_build_app())

        with patch(
            "src.presentation.api.middlewares.logging_middleware._SLOW_REQUEST_THRESHOLD_SECONDS",
            -1.0,
        ):
            with caplog.at_level(
                "WARNING",
                logger="src.presentation.api.middlewares.logging_middleware",
            ):
                response = client.get("/ok")

        assert response.status_code == 200
        assert any(record.message == "Slow request" for record in caplog.records)

    def test_logs_exception_and_reraises(self, caplog: pytest.LogCaptureFixture) -> None:
        client = TestClient(_build_app(), raise_server_exceptions=True)

        with caplog.at_level(
            "ERROR",
            logger="src.presentation.api.middlewares.logging_middleware",
        ):
            with pytest.raises(RuntimeError, match="boom"):
                client.get("/fail")

        assert any(record.message == "Request failed" for record in caplog.records)
