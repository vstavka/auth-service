import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.ports.system import UnitOfWork
from src.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAccountRepository,
    SQLSessionRepository,
)

logger = logging.getLogger(__name__)


class SQLUnitOfWork(UnitOfWork):
    """Transaction context with access to repositories."""

    accounts: SQLAccountRepository
    sessions: SQLSessionRepository
    _session: AsyncSession | None = None

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def begin(self) -> None:
        """Begin transaction."""
        if self._session is not None:
            raise RuntimeError("UnitOfWork is already active")
        self._session = self._session_factory()
        self.accounts = SQLAccountRepository(self._session)
        self.sessions = SQLSessionRepository(self._session)
        logger.debug("UnitOfWork started, session=%s", id(self._session))

    async def commit(self) -> None:
        await self._session.commit()
        logger.debug("UnitOfWork committed, session=%s", id(self._session))

    async def rollback(self) -> None:
        await self._session.rollback()
        logger.debug("UnitOfWork rolled back, session=%s", id(self._session))

    async def __aenter__(self) -> "SQLUnitOfWork":
        await self.begin()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """On success commit; on exception rollback; always close."""
        try:
            if exc_type is None:
                await self.commit()
            else:
                logger.error(
                    "UnitOfWork error, rolling back: %s: %s",
                    exc_type.__name__,
                    exc_value,
                    exc_info=(exc_type, exc_value, traceback),
                )
                await self.rollback()
        finally:
            await self._session.close()
            logger.debug("UnitOfWork session closed, session=%s", id(self._session))
            self._session = None
