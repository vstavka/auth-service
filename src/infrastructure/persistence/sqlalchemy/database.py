from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from src.infrastructure.persistence.sqlalchemy.models import Base


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


async def init_sqlite_schema(engine: AsyncEngine) -> None:
    """
    Создаёт таблицы напрямую через metadata.create_all — только для SQLite
    в локальной разработке/тестах. Для Postgres в проде схема управляется
    через Alembic-миграции, а не через этот механизм.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
