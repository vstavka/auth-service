import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from src.infrastructure.persistence.sqlalchemy.database import (
    create_engine,
    create_session_maker,
    init_sqlite_schema,
)


@pytest.mark.unit
class TestDatabaseHelpers:
    def test_create_engine_returns_async_engine_with_url(self) -> None:
        url = "sqlite+aiosqlite:///:memory:"
        engine = create_engine(url)

        try:
            assert isinstance(engine, AsyncEngine)
            assert str(engine.url) == url
        finally:
            # dispose is async — sync close via sync_engine for unit check
            engine.sync_engine.dispose()

    def test_create_session_maker_expire_on_commit_false(self) -> None:
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        try:
            session_maker = create_session_maker(engine)

            assert isinstance(session_maker, async_sessionmaker)
            assert session_maker.kw["expire_on_commit"] is False
        finally:
            engine.sync_engine.dispose()

    @pytest.mark.asyncio
    async def test_init_sqlite_schema_creates_account_table(self) -> None:
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        try:
            await init_sqlite_schema(engine)

            async with engine.connect() as conn:
                table_names = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )

            assert "account" in table_names
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_init_sqlite_schema_idempotent(self) -> None:
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        try:
            await init_sqlite_schema(engine)
            await init_sqlite_schema(engine)

            async with engine.connect() as conn:
                table_names = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )

            assert "account" in table_names
        finally:
            await engine.dispose()
