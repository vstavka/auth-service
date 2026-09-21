from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, register_user

pytestmark = pytest.mark.e2e


def test_list_sessions_returns_sessions_after_login(api_client: TestClient) -> None:
    register_user(api_client, email="sessions.user@example.com")
    login = api_client.post(
        "/v1/auth/login",
        json={
            "email": "sessions.user@example.com",
            "password": "StrongPassword123!",
        },
    )
    access_token = login.json()["access_token"]

    response = api_client.get(
        "/v1/sessions",
        headers=auth_header(access_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 2
    assert "id" in body[0]


def test_list_sessions_returns_401_without_token(api_client: TestClient) -> None:
    response = api_client.get("/v1/sessions")

    assert response.status_code == 401


def test_revoke_session_returns_204(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="revoke.one@example.com")
    headers = auth_header(tokens["access_token"])
    sessions = api_client.get("/v1/sessions", headers=headers).json()
    session_id = sessions[0]["id"]

    response = api_client.delete(f"/v1/sessions/{session_id}", headers=headers)

    assert response.status_code == 204


def test_revoke_session_returns_404_when_missing(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="revoke.missing@example.com")

    response = api_client.delete(
        f"/v1/sessions/{uuid4()}",
        headers=auth_header(tokens["access_token"]),
    )

    assert response.status_code == 404


def test_revoke_all_sessions_invalidates_refresh(api_client: TestClient) -> None:
    tokens = register_user(api_client, email="revoke.all@example.com")
    headers = auth_header(tokens["access_token"])

    response = api_client.delete("/v1/sessions", headers=headers)

    assert response.status_code == 204

    refresh = api_client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 401
