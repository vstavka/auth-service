import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, register_user

pytestmark = pytest.mark.e2e


def test_register_returns_201_with_token_pair(api_client: TestClient) -> None:
    body = register_user(api_client)

    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert isinstance(body["expires_in"], int)
    assert body["expires_in"] > 0


def test_register_returns_422_when_email_missing(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/register",
        json={"password": "StrongPassword123!"},
    )

    assert response.status_code == 422


def test_register_returns_422_when_password_missing(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/register",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 422


def test_register_returns_422_when_email_invalid(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/register",
        json={"email": "not-an-email", "password": "StrongPassword123!"},
    )

    assert response.status_code == 422


def test_register_returns_422_when_password_too_short(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "12345"},
    )

    assert response.status_code == 422


def test_register_returns_422_when_password_too_long(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "x" * 65},
    )

    assert response.status_code == 422


def test_register_path_requires_v1_prefix(api_client: TestClient) -> None:
    response = api_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 404


def test_login_returns_200_with_token_pair(api_client: TestClient) -> None:
    register_user(api_client, email="login.user@example.com")

    response = api_client.post(
        "/v1/auth/login",
        json={
            "email": "login.user@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_returns_401_for_invalid_credentials(api_client: TestClient) -> None:
    register_user(api_client, email="login.fail@example.com")

    response = api_client.post(
        "/v1/auth/login",
        json={
            "email": "login.fail@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_returns_422_when_schema_invalid(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/login",
        json={"email": "not-an-email", "password": "StrongPassword123!"},
    )

    assert response.status_code == 422


def test_refresh_returns_200_with_new_token_pair(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="refresh.user@example.com")

    response = api_client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != tokens["refresh_token"]


def test_refresh_returns_401_for_invalid_refresh_token(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/auth/refresh",
        json={"refresh_token": "not-a-valid-refresh-token"},
    )

    assert response.status_code == 401


def test_logout_returns_204(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="logout.user@example.com")

    response = api_client.post(
        "/v1/auth/logout",
        headers=auth_header(tokens["access_token"]),
    )

    assert response.status_code == 204


def test_logout_returns_401_without_token(api_client: TestClient) -> None:
    response = api_client.post("/v1/auth/logout")

    assert response.status_code == 401


def test_logout_is_idempotent_and_invalidates_refresh(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="logout.twice@example.com")
    headers = auth_header(tokens["access_token"])

    assert api_client.post("/v1/auth/logout", headers=headers).status_code == 204
    assert api_client.post("/v1/auth/logout", headers=headers).status_code == 204

    refresh = api_client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 401
