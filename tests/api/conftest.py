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


def register_user(
        client: TestClient,
        *,
        email: str = "new.user@example.com",
        password: str = "StrongPassword123!",
) -> dict:
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}
