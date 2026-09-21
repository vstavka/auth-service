from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.exceptions.auth import AccessTokenInvalidError
from src.domain.exceptions.email import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
)
from src.domain.exceptions.password import InvalidPasswordError
from src.presentation.api.exception_handlers import register_exception_handlers
from src.shared.errors.codes import ErrorCode


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/invalid-email")
    async def invalid_email() -> None:
        raise InvalidEmailError(details={"reason": "bad"})

    @app.get("/invalid-password")
    async def invalid_password() -> None:
        raise InvalidPasswordError(details={"reason": "too_short"})

    @app.get("/email-taken")
    async def email_taken() -> None:
        raise EmailAlreadyRegisteredError(details={"email": "a@b.com"})

    @app.get("/bad-token")
    async def bad_token() -> None:
        raise AccessTokenInvalidError()

    return app


@pytest.mark.unit
class TestAppErrorHandler:
    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(_build_app())

    def test_invalid_email_returns_422(self, client: TestClient) -> None:
        response = client.get("/invalid-email")

        assert response.status_code == 422
        assert response.json() == {
            "code": ErrorCode.AUTH_INVALID_EMAIL.value,
            "message": "Invalid email",
            "details": {"reason": "bad"},
        }

    def test_invalid_password_returns_422(self, client: TestClient) -> None:
        response = client.get("/invalid-password")

        assert response.status_code == 422
        body = response.json()
        assert body["code"] == ErrorCode.AUTH_INVALID_PASSWORD.value
        assert body["details"] == {"reason": "too_short"}

    def test_email_already_registered_returns_409(self, client: TestClient) -> None:
        response = client.get("/email-taken")

        assert response.status_code == 409
        assert response.json()["code"] == ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED.value

    def test_access_token_invalid_returns_401(self, client: TestClient) -> None:
        response = client.get("/bad-token")

        assert response.status_code == 401
        assert response.json()["code"] == ErrorCode.AUTH_ACCESS_TOKEN_INVALID.value
        assert response.json()["details"] is None


@pytest.mark.e2e
class TestRegisterDomainErrorsMapped:
    @pytest.fixture
    def api_client(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("JWT_SECRET_KEY", "handler-test-secret-key-long-enough")
        monkeypatch.setenv("DB_TYPE", "sqlite")
        monkeypatch.setenv("DB_NAME", "handler_auth")
        monkeypatch.setenv("LOGGING_LEVEL", "WARNING")

        from src.main import app

        with TestClient(app) as client:
            yield client

    def test_register_duplicate_email_returns_409(self, api_client: TestClient) -> None:
        payload = {
            "email": "dup@example.com",
            "password": "StrongPassword123!",
        }
        assert api_client.post("/v1/auth/register", json=payload).status_code == 200

        response = api_client.post("/v1/auth/register", json=payload)

        assert response.status_code == 409
        assert response.json()["code"] == ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED.value

    def test_register_weak_password_returns_422(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"email": "weak@example.com", "password": "password12345"},
        )

        assert response.status_code == 422
        body = response.json()
        # Pydantic min_length=6 пропускает, domain PasswordPolicy отклоняет
        assert body["code"] == ErrorCode.AUTH_INVALID_PASSWORD.value
        assert body["details"]["reason"] == "no_special_character"
