import logging
from abc import abstractmethod

from src.application.ports.account_repository import AccountRepository

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Transaction context with access to repositories."""
    account: AccountRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """On success commit; on exception rollback; always close."""
        await self.rollback()
