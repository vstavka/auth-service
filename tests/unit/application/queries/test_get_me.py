from datetime import UTC, datetime, timedelta
from uuid import UUID
import json

import pytest

from src.application.cache_keys import account_key
from src.application.dto import GetMeQuery
from src.application.queries import GetMeHandler
from src.domain.entities import Account
from src.domain.enums import AccountStatus
from src.domain.exceptions.auth import AccountDisabledError, UserNotFoundError
from src.domain.value_objects import Email, PasswordHash, UserId
from src.infrastructure.cache import InMemoryCache
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))


@pytest.mark.asyncio
class TestGetMe:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def cache(self) -> InMemoryCache:
        return InMemoryCache()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def handler(self, fake_uow: FakeUnitOfWork, cache: InMemoryCache) -> GetMeHandler:
        return GetMeHandler(uow=fake_uow, cache=cache, ttl=timedelta(minutes=1))

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

    async def test_cache_hit_skips_uow(
            self,
            handler: GetMeHandler,
            cache: InMemoryCache,
            fake_clock: FakeClock,
    ) -> None:
        payload = {
            "id": str(ACTOR_ID.value),
            "email": "cached@example.com",
            "status": "active",
            "created_at": fake_clock.now().isoformat(),
            "updated_at": fake_clock.now().isoformat(),
        }
        await cache.set(
            account_key(ACTOR_ID),
            json.dumps(payload).encode("utf-8"),
        )

        result = await handler.execute(GetMeQuery(actor_id=ACTOR_ID))

        assert result.email == "cached@example.com"

    async def test_broken_cache_falls_back_to_db(
            self,
            handler: GetMeHandler,
            fake_uow: FakeUnitOfWork,
            cache: InMemoryCache,
            fake_clock: FakeClock,
    ) -> None:
        account = Account.create(
            public_id=ACTOR_ID,
            email=Email("user@example.com"),
            password_hash=PasswordHash("hash"),
            now=fake_clock.now(),
        )
        await fake_uow.accounts.add(account)
        await cache.set(account_key(ACTOR_ID), b"not-json")

        result = await handler.execute(GetMeQuery(actor_id=ACTOR_ID))

        assert result.email == "user@example.com"
        assert await cache.get(account_key(ACTOR_ID)) is not None
