from abc import abstractmethod
from typing import Protocol

from src.application.ports.repositories.account_repository import AccountRepository


class UnitOfWork(Protocol):
    """Transaction context with access to repositories."""
    accounts: AccountRepository

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """On success commit; on exception rollback; always close."""
        await self.rollback()
