from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect


@pytest.fixture
def sqlite_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JWT_SECRET_KEY", "startup-test-secret-key")
    monkeypatch.setenv("DB_TYPE", "sqlite")
    monkeypatch.setenv("DB_NAME", "startup_auth")
    monkeypatch.setenv("LOGGING_LEVEL", "WARNING")


@pytest.mark.e2e
class TestAppStartup:
    def test_app_starts_and_register_route_available(
            self,
            sqlite_env: None,
    ) -> None:
        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "startup@example.com",
                    "password": "StrongPassword123!",
                },
            )
            assert response.status_code == 201

    def test_lifespan_wires_container_and_handler(self, sqlite_env: None) -> None:
        from src.application.commands import RegisterAccountHandler
        from src.main import app

        with TestClient(app) as client:
            assert hasattr(app, "container")
            handler = app.container.register_account_handler()
            assert isinstance(handler, RegisterAccountHandler)

            response = client.post(
                "/v1/auth/register",
                json={
                    "email": "wired@example.com",
                    "password": "StrongPassword123!",
                },
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_sqlite_schema_initialized_when_db_type_sqlite(
            self,
            sqlite_env: None,
    ) -> None:
        from src.main import app

        with TestClient(app):
            engine = app.container.engine()
            async with engine.connect() as conn:
                table_names = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )

            assert "account" in table_names
            assert "outbox_messages" in table_names
