from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.cache_keys import sessions_key
from src.application.commands import LoginAccountHandler
from src.application.dto import LoginRequest
from src.domain.entities import Account
from src.domain.exceptions.auth import AccountDisabledError, InvalidCredentialsError
from src.domain.exceptions.email import InvalidEmailError
from src.domain.value_objects import Email, UserId
from src.infrastructure.cache import InMemoryCache
from tests.fakes.security.fake_password_hasher import FakePasswordHasher
from tests.fakes.security.fake_token_service import FakeTokenService
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_id_generator import FakeIdGenerator
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

PASSWORD = "StrongPassword123!"
ACCOUNT_PUBLIC_ID = UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c")
SESSION_PUBLIC_ID = UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e")


@pytest.mark.asyncio
class TestLoginAccount:
    @pytest.fixture
    def fixed_now(self) -> datetime:
        return datetime(2026, 9, 16, 20, 0, tzinfo=UTC)

    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self, fixed_now: datetime) -> FakeClock:
        return FakeClock(fixed_now)

    @pytest.fixture
    def fake_id_generator(self) -> FakeIdGenerator:
        return FakeIdGenerator(ids=[SESSION_PUBLIC_ID])

    @pytest.fixture
    def fake_password_hasher(self) -> FakePasswordHasher:
        return FakePasswordHasher()

    @pytest.fixture
    def fake_token_service(self, fake_clock: FakeClock) -> FakeTokenService:
        return FakeTokenService(clock=fake_clock)

    @pytest.fixture
    def handler(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            fake_id_generator: FakeIdGenerator,
            fake_password_hasher: FakePasswordHasher,
            fake_token_service: FakeTokenService,
    ) -> LoginAccountHandler:
        return LoginAccountHandler(
            uow=fake_uow,
            password_hasher=fake_password_hasher,
            token_service=fake_token_service,
            id_generator=fake_id_generator,
            clock=fake_clock,
            cache=InMemoryCache(),
        )

    async def _seed_account(
            self,
            fake_uow: FakeUnitOfWork,
            fake_password_hasher: FakePasswordHasher,
            fake_clock: FakeClock,
    ) -> Account:
        account = Account.create(
            public_id=UserId(ACCOUNT_PUBLIC_ID),
            email=Email("user@example.com"),
            password_hash=fake_password_hasher.hash(PASSWORD),
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        return account

    async def test_logs_in_and_creates_session(
            self,
            handler: LoginAccountHandler,
            fake_uow: FakeUnitOfWork,
            fake_password_hasher: FakePasswordHasher,
            fake_clock: FakeClock,
            fake_token_service: FakeTokenService,
    ) -> None:
        account = await self._seed_account(fake_uow, fake_password_hasher, fake_clock)

        result = await handler.execute(
            LoginRequest(
                email="User@Example.COM",
                password=PASSWORD,
                ip="203.0.113.10",
            )
        )

        sessions = await fake_uow.sessions.list_by_account_id(account.id)
        assert len(sessions) == 1
        assert sessions[0].ip == "203.0.113.10"
        assert sessions[0].public_id.value == SESSION_PUBLIC_ID
        assert result.refresh_token
        assert result.access_token_expires_at == fake_clock.now() + fake_token_service._access_token_ttl
        assert fake_uow.commit_called is True

    async def test_rejects_unknown_email(
            self,
            handler: LoginAccountHandler,
            fake_uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidCredentialsError):
            await handler.execute(
                LoginRequest(email="missing@example.com", password=PASSWORD)
            )

        assert fake_uow.commit_called is False
        assert await fake_uow.sessions.list_by_account_id(1) == []

    async def test_rejects_wrong_password(
            self,
            handler: LoginAccountHandler,
            fake_uow: FakeUnitOfWork,
            fake_password_hasher: FakePasswordHasher,
            fake_clock: FakeClock,
    ) -> None:
        await self._seed_account(fake_uow, fake_password_hasher, fake_clock)

        with pytest.raises(InvalidCredentialsError):
            await handler.execute(
                LoginRequest(email="user@example.com", password="WrongPassword123!")
            )

        assert fake_uow.commit_called is False

    async def test_rejects_disabled_account(
            self,
            handler: LoginAccountHandler,
            fake_uow: FakeUnitOfWork,
            fake_password_hasher: FakePasswordHasher,
            fake_clock: FakeClock,
    ) -> None:
        account = await self._seed_account(fake_uow, fake_password_hasher, fake_clock)
        account.disable(fake_clock.now())

        with pytest.raises(AccountDisabledError):
            await handler.execute(
                LoginRequest(email="user@example.com", password=PASSWORD)
            )

    async def test_rejects_invalid_email(self, handler: LoginAccountHandler) -> None:
        with pytest.raises(InvalidEmailError):
            await handler.execute(
                LoginRequest(email="not-an-email", password=PASSWORD)
            )

    async def test_invalidates_sessions_cache(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            fake_id_generator: FakeIdGenerator,
            fake_password_hasher: FakePasswordHasher,
            fake_token_service: FakeTokenService,
    ) -> None:
        cache = InMemoryCache()
        await self._seed_account(fake_uow, fake_password_hasher, fake_clock)
        await cache.set(sessions_key(UserId(ACCOUNT_PUBLIC_ID)), b"stale")
        handler = LoginAccountHandler(
            uow=fake_uow,
            password_hasher=fake_password_hasher,
            token_service=fake_token_service,
            id_generator=fake_id_generator,
            clock=fake_clock,
            cache=cache,
        )

        await handler.execute(LoginRequest(email="user@example.com", password=PASSWORD))

        assert await cache.get(sessions_key(UserId(ACCOUNT_PUBLIC_ID))) is None
