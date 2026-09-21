import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, register_user

pytestmark = pytest.mark.e2e


def test_get_me_returns_200(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="me.user@example.com")

    response = api_client.get(
        "/v1/me",
        headers=auth_header(tokens["access_token"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me.user@example.com"
    assert body["status"] == "active"
    assert body["id"]


def test_get_me_returns_401_without_token(api_client: TestClient) -> None:
    response = api_client.get("/v1/me")

    assert response.status_code == 401


def test_change_email_returns_200(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="old.email@example.com")

    response = api_client.patch(
        "/v1/me/email",
        headers=auth_header(tokens["access_token"]),
        json={"email": "new.email@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new.email@example.com"


def test_change_email_returns_409_when_duplicate(api_client: TestClient) -> None:
    register_user(api_client, email="taken@example.com")
    tokens = register_user(api_client, email="changer@example.com")

    response = api_client.patch(
        "/v1/me/email",
        headers=auth_header(tokens["access_token"]),
        json={"email": "taken@example.com"},
    )

    assert response.status_code == 409


def test_change_email_returns_401_without_token(api_client: TestClient) -> None:
    response = api_client.patch(
        "/v1/me/email",
        json={"email": "someone@example.com"},
    )

    assert response.status_code == 401


def test_change_password_returns_204(api_client: TestClient) -> None:
    tokens = register_user(
        api_client,
        email="pwd.user@example.com",
        password="StrongPassword123!",
    )

    response = api_client.patch(
        "/v1/me/password",
        headers=auth_header(tokens["access_token"]),
        json={
            "current_password": "StrongPassword123!",
            "new_password": "AnotherStrong123!",
        },
    )

    assert response.status_code == 204

    login = api_client.post(
        "/v1/auth/login",
        json={"email": "pwd.user@example.com", "password": "AnotherStrong123!"},
    )
    assert login.status_code == 200


def test_change_password_returns_401_for_wrong_current(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="pwd.wrong@example.com")

    response = api_client.patch(
        "/v1/me/password",
        headers=auth_header(tokens["access_token"]),
        json={
            "current_password": "WrongPassword123!",
            "new_password": "AnotherStrong123!",
        },
    )

    assert response.status_code == 401


def test_change_password_returns_422_for_weak_new(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="pwd.weak@example.com")

    response = api_client.patch(
        "/v1/me/password",
        headers=auth_header(tokens["access_token"]),
        json={
            "current_password": "StrongPassword123!",
            "new_password": "password12345",
        },
    )

    assert response.status_code == 422
