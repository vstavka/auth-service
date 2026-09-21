from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JWT_SECRET_KEY", "api-test-secret-key-long-enough")
    monkeypatch.setenv("DB_TYPE", "sqlite")
    monkeypatch.setenv("DB_NAME", "api_auth")
    monkeypatch.setenv("APP_NAME", "auth-service")
    monkeypatch.setenv("LOGGING_LEVEL", "WARNING")

    from src.main import app

    with TestClient(app) as client:
        yield client


@pytest.mark.e2e
class TestRegisterEndpoint:
    def test_register_returns_200_with_token_pair(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={
                "email": "new.user@example.com",
                "password": "StrongPassword123!",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"
        assert isinstance(body["expires_in"], int)
        assert body["expires_in"] > 0

    def test_register_returns_422_when_email_missing(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"password": "StrongPassword123!"},
        )

        assert response.status_code == 422

    def test_register_returns_422_when_password_missing(
            self,
            api_client: TestClient,
    ) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"email": "user@example.com"},
        )

        assert response.status_code == 422

    def test_register_returns_422_when_email_invalid(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"email": "not-an-email", "password": "StrongPassword123!"},
        )

        assert response.status_code == 422

    def test_register_returns_422_when_password_too_short(
            self,
            api_client: TestClient,
    ) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"email": "user@example.com", "password": "12345"},
        )

        assert response.status_code == 422

    def test_register_returns_422_when_password_too_long(
            self,
            api_client: TestClient,
    ) -> None:
        response = api_client.post(
            "/v1/auth/register",
            json={"email": "user@example.com", "password": "x" * 65},
        )

        assert response.status_code == 422

    def test_register_path_requires_v1_prefix(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "StrongPassword123!",
            },
        )

        assert response.status_code == 404
