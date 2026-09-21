import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

from src.infrastructure.persistence.sqlalchemy.models import Base


@pytest_asyncio.fixture
async def async_engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(async_engine: AsyncEngine) -> AsyncSession:
    """
    Сессия для тестов, которые не тестируют сам commit/rollback,
    а просто читают/пишут данные и откатывают всё в конце теста.
    """
    async_session = AsyncSession(async_engine, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()


@pytest_asyncio.fixture
def session_factory(async_engine: AsyncEngine):
    """
    Фабрика сессий — нужна для SQLUnitOfWork, который сам создаёт
    и закрывает сессии внутри begin()/__aexit__().
    """
    def factory() -> AsyncSession:
        return AsyncSession(async_engine, expire_on_commit=False)

    return factory