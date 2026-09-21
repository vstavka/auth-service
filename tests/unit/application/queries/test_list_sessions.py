from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.dto import ListSessionsQuery
from src.application.queries import ListSessionsHandler
from src.domain.entities import Account, Session
from src.domain.exceptions.auth import UserNotFoundError
from src.domain.value_objects import Email, PasswordHash, RefreshTokenHash, SessionId, UserId
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))
OTHER_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"))
SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e"))
REVOKED_SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190f"))
FOREIGN_SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c61911"))


@pytest.mark.asyncio
class TestListSessions:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def handler(self, fake_uow: FakeUnitOfWork) -> ListSessionsHandler:
        return ListSessionsHandler(uow=fake_uow)

    async def test_returns_own_sessions_including_revoked(
            self,
            handler: ListSessionsHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        now = fake_clock.now()
        account = Account.create(
            public_id=ACTOR_ID,
            email=Email("user@example.com"),
            password_hash=PasswordHash("hash"),
            now=now,
        )
        other = Account.create(
            public_id=OTHER_ID,
            email=Email("other@example.com"),
            password_hash=PasswordHash("hash"),
            now=now,
        )
        await fake_uow.accounts.add(account)
        await fake_uow.accounts.add(other)

        active = Session.create(
            public_id=SESSION_ID,
            account_id=account.id,
            refresh_token_hash=RefreshTokenHash("a" * 64),
            now=now,
            expires_at=now + timedelta(days=7),
        )
        revoked = Session.create(
            public_id=REVOKED_SESSION_ID,
            account_id=account.id,
            refresh_token_hash=RefreshTokenHash("b" * 64),
            now=now,
            expires_at=now + timedelta(days=7),
        )
        revoked.revoke(now)
        foreign = Session.create(
            public_id=FOREIGN_SESSION_ID,
            account_id=other.id,
            refresh_token_hash=RefreshTokenHash("c" * 64),
            now=now,
            expires_at=now + timedelta(days=7),
        )
        await fake_uow.sessions.add(active)
        await fake_uow.sessions.add(revoked)
        await fake_uow.sessions.add(foreign)

        result = await handler.execute(ListSessionsQuery(actor_id=ACTOR_ID))

        ids = {item.id for item in result}
        assert ids == {SESSION_ID.value, REVOKED_SESSION_ID.value}
        revoked_item = next(item for item in result if item.id == REVOKED_SESSION_ID.value)
        assert revoked_item.revoked_at == now

    async def test_unknown_actor(self, handler: ListSessionsHandler) -> None:
        with pytest.raises(UserNotFoundError):
            await handler.execute(ListSessionsQuery(actor_id=ACTOR_ID))
