from types import TracebackType

from src.application.ports.system.unit_of_work import UnitOfWork
from tests.fakes.repositories import FakeAccountRepository, FakeSessionRepository


class FakeUnitOfWork(UnitOfWork):
    def __init__(self):
        self.commit_called = False
        self.rollback_called = False
        self.closed = False
        self.accounts = FakeAccountRepository()
        self.sessions = FakeSessionRepository()

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

        self.closed = True

    async def commit(self) -> None:
        self.commit_called = True

    async def rollback(self) -> None:
        self.rollback_called = True
