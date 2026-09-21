from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.commands import RefreshTokensHandler
from src.application.dto import RefreshTokensRequest
from src.domain.entities import Account, Session
from src.domain.exceptions.auth import AccountDisabledError, RefreshTokenInvalidError
from src.domain.value_objects import Email, PasswordHash, RefreshTokenHash, SessionId, UserId
from tests.fakes.security.fake_token_service import FakeTokenService
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))
SESSION_PUBLIC_ID = SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e"))
RAW_REFRESH = "raw-refresh-token"


@pytest.mark.asyncio
class TestRefreshTokens:
    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self) -> FakeClock:
        return FakeClock(datetime(2026, 9, 16, 20, 0, tzinfo=UTC))

    @pytest.fixture
    def fake_token_service(self, fake_clock: FakeClock) -> FakeTokenService:
        return FakeTokenService(clock=fake_clock)

    @pytest.fixture
    def handler(
            self,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
    ) -> RefreshTokensHandler:
        return RefreshTokensHandler(
            uow=fake_uow,
            token_service=fake_token_service,
            clock=fake_clock,
        )

    async def _seed(
            self,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
            *,
            disabled: bool = False,
            revoked: bool = False,
            expired: bool = False,
    ) -> Session:
        now = fake_clock.now()
        account = Account.create(
            public_id=ACTOR_ID,
            email=Email("user@example.com"),
            password_hash=PasswordHash("hash"),
            now=now,
        )
        await fake_uow.accounts.add(account)
        if disabled:
            account.disable(now)
        expires_at = now - timedelta(seconds=1) if expired else now + timedelta(days=7)
        session = Session(
            id=None,
            public_id=SESSION_PUBLIC_ID,
            account_id=account.id,
            refresh_token_hash=RefreshTokenHash(
                fake_token_service.hash_refresh_token(RAW_REFRESH),
            ),
            ip=None,
            user_agent=None,
            device_info=None,
            created_at=now - timedelta(days=1),
            expires_at=expires_at,
            revoked_at=now if revoked else None,
        )
        await fake_uow.sessions.add(session)
        return session

    async def test_issues_new_token_pair_and_rotates_refresh(
            self,
            handler: RefreshTokensHandler,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
    ) -> None:
        session = await self._seed(fake_uow, fake_token_service, fake_clock)

        result = await handler.execute(RefreshTokensRequest(refresh_token=RAW_REFRESH))

        assert result.access_token
        assert result.refresh_token
        assert result.refresh_token != RAW_REFRESH
        stored = await fake_uow.sessions.get_by_public_id(SESSION_PUBLIC_ID)
        assert stored is not None
        assert stored.refresh_token_hash == RefreshTokenHash(
            fake_token_service.hash_refresh_token(result.refresh_token),
        )
        assert stored.expires_at == result.refresh_token_expires_at
        assert stored.public_id == session.public_id
        assert await fake_uow.sessions.get_by_refresh_token_hash(
            RefreshTokenHash(fake_token_service.hash_refresh_token(RAW_REFRESH)),
        ) is None
        assert fake_uow.commit_called is True

    async def test_rejects_unknown_refresh_token(
            self,
            handler: RefreshTokensHandler,
    ) -> None:
        with pytest.raises(RefreshTokenInvalidError):
            await handler.execute(RefreshTokensRequest(refresh_token="missing"))

    async def test_rejects_revoked_session(
            self,
            handler: RefreshTokensHandler,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
    ) -> None:
        await self._seed(fake_uow, fake_token_service, fake_clock, revoked=True)

        with pytest.raises(RefreshTokenInvalidError):
            await handler.execute(RefreshTokensRequest(refresh_token=RAW_REFRESH))

    async def test_rejects_expired_session(
            self,
            handler: RefreshTokensHandler,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
    ) -> None:
        await self._seed(fake_uow, fake_token_service, fake_clock, expired=True)

        with pytest.raises(RefreshTokenInvalidError):
            await handler.execute(RefreshTokensRequest(refresh_token=RAW_REFRESH))

    async def test_rejects_disabled_account(
            self,
            handler: RefreshTokensHandler,
            fake_uow: FakeUnitOfWork,
            fake_token_service: FakeTokenService,
            fake_clock: FakeClock,
    ) -> None:
        await self._seed(fake_uow, fake_token_service, fake_clock, disabled=True)

        with pytest.raises(AccountDisabledError):
            await handler.execute(RefreshTokensRequest(refresh_token=RAW_REFRESH))
