from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.dto import GetMeQuery
from src.application.queries import GetMeHandler
from src.domain.entities import Account
from src.domain.enums import AccountStatus
from src.domain.exceptions.auth import AccountDisabledError, UserNotFoundError
from src.domain.value_objects import Email, PasswordHash, UserId
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))


@pytest.mark.asyncio
class TestGetMe:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def handler(self, fake_uow: FakeUnitOfWork) -> GetMeHandler:
        return GetMeHandler(uow=fake_uow)

    async def test_returns_public_account(
            self,
            handler: GetMeHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        account = Account.create(
            public_id=ACTOR_ID,
            email=Email("User@Example.COM"),
            password_hash=PasswordHash("hash"),
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)

        result = await handler.execute(GetMeQuery(actor_id=ACTOR_ID))

        assert result.id == ACTOR_ID.value
        assert result.email == "user@example.com"
        assert result.status is AccountStatus.ACTIVE
        assert result.created_at == fake_clock.now()
        assert result.updated_at == fake_clock.now()

    async def test_unknown_actor(self, handler: GetMeHandler) -> None:
        with pytest.raises(UserNotFoundError):
            await handler.execute(GetMeQuery(actor_id=ACTOR_ID))

    async def test_rejects_disabled_account(
            self,
            handler: GetMeHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        account = Account.create(
            public_id=ACTOR_ID,
            email=Email("user@example.com"),
            password_hash=PasswordHash("hash"),
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        account.disable(fake_clock.now())

        with pytest.raises(AccountDisabledError):
            await handler.execute(GetMeQuery(actor_id=ACTOR_ID))
