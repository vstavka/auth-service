from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.commands import RevokeAllSessionsHandler, RevokeSessionHandler
from src.application.dto import RevokeAllSessionsRequest, RevokeSessionRequest
from src.domain.entities import Account, Session
from src.domain.exceptions.auth import SessionNotFoundError, UserNotFoundError
from src.domain.value_objects import Email, PasswordHash, RefreshTokenHash, SessionId, UserId
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))
OTHER_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"))
SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e"))
OTHER_SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190f"))


def _make_account(public_id: UserId, email: str, now: datetime) -> Account:
    return Account.create(
        public_id=public_id,
        email=Email(email),
        password_hash=PasswordHash("hash"),
        now=now,
    )


def _make_session(*, public_id: SessionId, account_id: int, token_hash: str, now: datetime) -> Session:
    return Session.create(
        public_id=public_id,
        account_id=account_id,
        refresh_token_hash=RefreshTokenHash(token_hash),
        now=now,
        expires_at=now + timedelta(days=7),
    )


@pytest.mark.asyncio
class TestRevokeSession:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def handler(self, fake_uow: FakeUnitOfWork, fake_clock: FakeClock) -> RevokeSessionHandler:
        return RevokeSessionHandler(uow=fake_uow, clock=fake_clock)

    async def test_revokes_own_session(
            self,
            handler: RevokeSessionHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        account = _make_account(ACTOR_ID, "user@example.com", fake_clock.now())
        await fake_uow.accounts.add(account)
        session = _make_session(
            public_id=SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(session)

        await handler.execute(RevokeSessionRequest(actor_id=ACTOR_ID, session_id=SESSION_ID))

        stored = await fake_uow.sessions.get_by_public_id(SESSION_ID)
        assert stored is not None
        assert stored.revoked_at == fake_clock.now()
        assert fake_uow.commit_called is True

    async def test_revoking_twice_is_noop(
            self,
            handler: RevokeSessionHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        account = _make_account(ACTOR_ID, "user@example.com", fake_clock.now())
        await fake_uow.accounts.add(account)
        session = _make_session(
            public_id=SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(session)
        first_revoked_at = datetime(2026, 9, 16, 19, 0, tzinfo=UTC)
        session.revoke(first_revoked_at)

        await handler.execute(RevokeSessionRequest(actor_id=ACTOR_ID, session_id=SESSION_ID))

        stored = await fake_uow.sessions.get_by_public_id(SESSION_ID)
        assert stored is not None
        assert stored.revoked_at == first_revoked_at

    async def test_foreign_session_looks_missing(
            self,
            handler: RevokeSessionHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        actor = _make_account(ACTOR_ID, "user@example.com", fake_clock.now())
        other = _make_account(OTHER_ID, "other@example.com", fake_clock.now())
        await fake_uow.accounts.add(actor)
        await fake_uow.accounts.add(other)
        foreign = _make_session(
            public_id=OTHER_SESSION_ID,
            account_id=other.id,
            token_hash="b" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(foreign)

        with pytest.raises(SessionNotFoundError):
            await handler.execute(
                RevokeSessionRequest(actor_id=ACTOR_ID, session_id=OTHER_SESSION_ID)
            )

        stored = await fake_uow.sessions.get_by_public_id(OTHER_SESSION_ID)
        assert stored is not None
        assert stored.revoked_at is None

    async def test_unknown_actor(
            self,
            handler: RevokeSessionHandler,
    ) -> None:
        with pytest.raises(UserNotFoundError):
            await handler.execute(
                RevokeSessionRequest(actor_id=ACTOR_ID, session_id=SESSION_ID)
            )


@pytest.mark.asyncio
class TestRevokeAllSessions:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    async def test_revokes_all_own_sessions(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
    ) -> None:
        handler = RevokeAllSessionsHandler(uow=fake_uow, clock=fake_clock)
        account = _make_account(ACTOR_ID, "user@example.com", fake_clock.now())
        other = _make_account(OTHER_ID, "other@example.com", fake_clock.now())
        await fake_uow.accounts.add(account)
        await fake_uow.accounts.add(other)
        first = _make_session(
            public_id=SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        second = _make_session(
            public_id=SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c61911")),
            account_id=account.id,
            token_hash="b" * 64,
            now=fake_clock.now(),
        )
        foreign = _make_session(
            public_id=OTHER_SESSION_ID,
            account_id=other.id,
            token_hash="c" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(first)
        await fake_uow.sessions.add(second)
        await fake_uow.sessions.add(foreign)

        await handler.execute(RevokeAllSessionsRequest(actor_id=ACTOR_ID))

        own = await fake_uow.sessions.list_by_account_id(account.id)
        assert all(item.is_revoked for item in own)
        foreign_stored = await fake_uow.sessions.get_by_public_id(OTHER_SESSION_ID)
        assert foreign_stored is not None
        assert foreign_stored.revoked_at is None
