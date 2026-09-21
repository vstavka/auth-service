import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.middlewares.request_id_middleware import RequestIDMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/ping")
    async def ping(request: Request) -> dict:
        return {"request_id": request.state.request_id}

    return app


@pytest.mark.unit
class TestRequestIDMiddleware:
    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(_build_app())

    def test_valid_x_request_id_echoed_in_response(self, client: TestClient) -> None:
        response = client.get("/ping", headers={"X-Request-ID": "abc-123"})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == "abc-123"
        assert response.json()["request_id"] == "abc-123"

    def test_missing_x_request_id_generates_new_id(self, client: TestClient) -> None:
        response = client.get("/ping")

        assert response.status_code == 200
        assert response.headers["X-Request-ID"]
        assert response.json()["request_id"] == response.headers["X-Request-ID"]

    def test_empty_x_request_id_generates_new_id(self, client: TestClient) -> None:
        response = client.get("/ping", headers={"X-Request-ID": ""})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"]

    def test_invalid_x_request_id_with_special_chars_generates_new_id(
            self,
            client: TestClient,
    ) -> None:
        response = client.get("/ping", headers={"X-Request-ID": "bad id!"})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] != "bad id!"

    def test_x_request_id_longer_than_64_generates_new_id(
            self,
            client: TestClient,
    ) -> None:
        too_long = "a" * 65
        response = client.get("/ping", headers={"X-Request-ID": too_long})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] != too_long

    def test_request_state_request_id_set_for_downstream(
            self,
            client: TestClient,
    ) -> None:
        response = client.get("/ping", headers={"X-Request-ID": "downstream-1"})

        assert response.json()["request_id"] == "downstream-1"
