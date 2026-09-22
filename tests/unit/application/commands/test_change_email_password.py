from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.cache_keys import account_key, sessions_key
from src.application.commands import ChangeEmailHandler, ChangePasswordHandler
from src.application.dto import ChangeEmailRequest, ChangePasswordRequest
from src.domain.entities import Account, Session
from src.domain.exceptions.auth import InvalidCredentialsError, SessionNotFoundError, UserNotFoundError
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.exceptions.password import InvalidPasswordError
from src.domain.services.password_policy import PasswordPolicy
from src.domain.value_objects import Email, RefreshTokenHash, SessionId, UserId
from src.infrastructure.cache import InMemoryCache
from tests.fakes.security.fake_password_hasher import FakePasswordHasher
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))
OTHER_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"))
CURRENT_SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e"))
OTHER_SESSION_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190f"))
PASSWORD = "StrongPassword123!"
NEW_PASSWORD = "AnotherPassword123!"


def _make_account(
        *,
        public_id: UserId,
        email: str,
        hasher: FakePasswordHasher,
        now: datetime,
) -> Account:
    return Account.create(
        public_id=public_id,
        email=Email(email),
        password_hash=hasher.hash(PASSWORD),
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
class TestChangeEmail:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def hasher(self) -> FakePasswordHasher:
        return FakePasswordHasher()

    @pytest.fixture
    def cache(self) -> InMemoryCache:
        return InMemoryCache()

    @pytest.fixture
    def handler(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            cache: InMemoryCache,
    ) -> ChangeEmailHandler:
        return ChangeEmailHandler(uow=fake_uow, clock=fake_clock, cache=cache)

    async def test_changes_email(
            self,
            handler: ChangeEmailHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        account = _make_account(
            public_id=ACTOR_ID,
            email="old@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)

        result = await handler.execute(
            ChangeEmailRequest(actor_id=ACTOR_ID, email="New@Example.COM")
        )

        stored = await fake_uow.accounts.get_by_id(ACTOR_ID)
        assert stored is not None
        assert stored.email == Email("new@example.com")
        assert result.id == ACTOR_ID.value
        assert result.email == "new@example.com"
        assert fake_uow.commit_called is True

    async def test_invalidates_account_cache(
            self,
            handler: ChangeEmailHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
            cache: InMemoryCache,
    ) -> None:
        account = _make_account(
            public_id=ACTOR_ID,
            email="old@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        await cache.set(account_key(ACTOR_ID), b"stale")

        await handler.execute(
            ChangeEmailRequest(actor_id=ACTOR_ID, email="new@example.com")
        )

        assert await cache.get(account_key(ACTOR_ID)) is None

    async def test_rejects_taken_email(
            self,
            handler: ChangeEmailHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        actor = _make_account(
            public_id=ACTOR_ID,
            email="old@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        other = _make_account(
            public_id=OTHER_ID,
            email="taken@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(actor)
        await fake_uow.accounts.add(other)

        with pytest.raises(EmailAlreadyRegisteredError):
            await handler.execute(
                ChangeEmailRequest(actor_id=ACTOR_ID, email="taken@example.com")
            )

    async def test_unknown_actor(self, handler: ChangeEmailHandler) -> None:
        with pytest.raises(UserNotFoundError):
            await handler.execute(
                ChangeEmailRequest(actor_id=ACTOR_ID, email="new@example.com")
            )


@pytest.mark.asyncio
class TestChangePassword:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def hasher(self) -> FakePasswordHasher:
        return FakePasswordHasher()

    @pytest.fixture
    def handler(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> ChangePasswordHandler:
        return ChangePasswordHandler(
            uow=fake_uow,
            password_policy=PasswordPolicy(),
            password_hasher=hasher,
            clock=fake_clock,
            cache=InMemoryCache(),
        )

    async def test_changes_password_and_revokes_other_sessions(
            self,
            handler: ChangePasswordHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        account = _make_account(
            public_id=ACTOR_ID,
            email="user@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        current = _make_session(
            public_id=CURRENT_SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        other = _make_session(
            public_id=OTHER_SESSION_ID,
            account_id=account.id,
            token_hash="b" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(current)
        await fake_uow.sessions.add(other)

        await handler.execute(
            ChangePasswordRequest(
                actor_id=ACTOR_ID,
                current_password=PASSWORD,
                new_password=NEW_PASSWORD,
                current_session_id=CURRENT_SESSION_ID,
            )
        )

        stored_account = await fake_uow.accounts.get_by_id(ACTOR_ID)
        assert stored_account is not None
        assert hasher.verify(NEW_PASSWORD, stored_account.password_hash)
        current_stored = await fake_uow.sessions.get_by_public_id(CURRENT_SESSION_ID)
        other_stored = await fake_uow.sessions.get_by_public_id(OTHER_SESSION_ID)
        assert current_stored is not None
        assert other_stored is not None
        assert current_stored.revoked_at is None
        assert other_stored.is_revoked is True

    async def test_rejects_wrong_current_password(
            self,
            handler: ChangePasswordHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        account = _make_account(
            public_id=ACTOR_ID,
            email="user@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        session = _make_session(
            public_id=CURRENT_SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(session)

        with pytest.raises(InvalidCredentialsError):
            await handler.execute(
                ChangePasswordRequest(
                    actor_id=ACTOR_ID,
                    current_password="WrongPassword123!",
                    new_password=NEW_PASSWORD,
                    current_session_id=CURRENT_SESSION_ID,
                )
            )

    async def test_rejects_foreign_current_session(
            self,
            handler: ChangePasswordHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        account = _make_account(
            public_id=ACTOR_ID,
            email="user@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        other = _make_account(
            public_id=OTHER_ID,
            email="other@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
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
                ChangePasswordRequest(
                    actor_id=ACTOR_ID,
                    current_password=PASSWORD,
                    new_password=NEW_PASSWORD,
                    current_session_id=OTHER_SESSION_ID,
                )
            )

    async def test_rejects_weak_new_password(
            self,
            handler: ChangePasswordHandler,
    ) -> None:
        with pytest.raises(InvalidPasswordError):
            await handler.execute(
                ChangePasswordRequest(
                    actor_id=ACTOR_ID,
                    current_password=PASSWORD,
                    new_password="123",
                    current_session_id=CURRENT_SESSION_ID,
                )
            )

    async def test_invalidates_account_and_sessions_cache(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            hasher: FakePasswordHasher,
    ) -> None:
        cache = InMemoryCache()
        handler = ChangePasswordHandler(
            uow=fake_uow,
            password_policy=PasswordPolicy(),
            password_hasher=hasher,
            clock=fake_clock,
            cache=cache,
        )
        account = _make_account(
            public_id=ACTOR_ID,
            email="user@example.com",
            hasher=hasher,
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        session = _make_session(
            public_id=CURRENT_SESSION_ID,
            account_id=account.id,
            token_hash="a" * 64,
            now=fake_clock.now(),
        )
        await fake_uow.sessions.add(session)
        await cache.set(account_key(ACTOR_ID), b"stale-account")
        await cache.set(sessions_key(ACTOR_ID), b"stale-sessions")

        await handler.execute(
            ChangePasswordRequest(
                actor_id=ACTOR_ID,
                current_password=PASSWORD,
                new_password=NEW_PASSWORD,
                current_session_id=CURRENT_SESSION_ID,
            )
        )

        assert await cache.get(account_key(ACTOR_ID)) is None
        assert await cache.get(sessions_key(ACTOR_ID)) is None
