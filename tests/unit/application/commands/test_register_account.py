from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.commands import RegisterAccountHandler
from src.application.dto import RegisterRequest, session_to_public
from src.domain.entities import Account
from src.domain.enums import AccountStatus
from src.domain.exceptions.email import EmailAlreadyRegisteredError, InvalidEmailError
from src.domain.exceptions.password import InvalidPasswordError
from src.domain.services.password_policy import PasswordPolicy
from src.domain.value_objects import Email, RefreshTokenHash, SessionId, UserId
from tests.fakes.security.fake_password_hasher import FakePasswordHasher
from tests.fakes.security.fake_token_service import FakeTokenService
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_id_generator import FakeIdGenerator
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork


@pytest.mark.asyncio
class TestRegisterAccount:
    @pytest.fixture
    def fixed_now(self) -> datetime:
        return datetime(2026, 9, 16, 20, 0, tzinfo=UTC)

    @pytest.fixture
    def account_id(self) -> UUID:
        return UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c")

    @pytest.fixture
    def session_id(self) -> UUID:
        return UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190e")

    @pytest.fixture
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self, fixed_now: datetime) -> FakeClock:
        return FakeClock(fixed_now)

    @pytest.fixture
    def fake_id_generator(
            self,
            account_id: UUID,
            session_id: UUID,
    ) -> FakeIdGenerator:
        return FakeIdGenerator(ids=[account_id, session_id])

    @pytest.fixture
    def fake_password_hasher(self) -> FakePasswordHasher:
        return FakePasswordHasher()

    @pytest.fixture
    def fake_token_service(
            self,
            fake_clock: FakeClock,
    ) -> FakeTokenService:
        return FakeTokenService(clock=fake_clock)

    @pytest.fixture
    def use_case(
            self,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            fake_id_generator: FakeIdGenerator,
            fake_password_hasher: FakePasswordHasher,
            fake_token_service: FakeTokenService,
    ) -> RegisterAccountHandler:
        return RegisterAccountHandler(
            uow=fake_uow,
            password_policy=PasswordPolicy(),
            password_hasher=fake_password_hasher,
            token_service=fake_token_service,
            id_generator=fake_id_generator,
            clock=fake_clock,
        )

    async def test_registers_new_account_and_returns_tokens(
            self,
            use_case: RegisterAccountHandler,
            fake_uow: FakeUnitOfWork,
            fake_password_hasher: FakePasswordHasher,
            fake_token_service: FakeTokenService,
            account_id: UUID,
            session_id: UUID,
            fixed_now: datetime,
    ) -> None:
        raw_password = "StrongPassword123!"
        result = await use_case.execute(
            RegisterRequest(
                email="User@Example.COM",
                password=raw_password,
            )
        )

        account = await fake_uow.accounts.get_by_id(
            UserId(account_id),
        )

        assert account is not None
        assert account.id is not None
        assert account.public_id == UserId(account_id)
        assert account.email == Email("user@example.com")
        assert account.status is AccountStatus.ACTIVE
        assert account.password_hash.value != raw_password
        assert account.password_hash == fake_password_hasher.hash(raw_password)
        assert account.created_at == fixed_now
        assert account.updated_at == fixed_now

        sessions = await fake_uow.sessions.list_by_account_id(account.id)
        assert len(sessions) == 1
        session = sessions[0]
        assert session.public_id == SessionId(session_id)
        assert session.account_id == account.id
        assert session.refresh_token_hash == RefreshTokenHash(
            fake_token_service.hash_refresh_token(result.refresh_token),
        )
        assert session.expires_at == result.refresh_token_expires_at
        assert session.ip is None
        assert session.user_agent is None
        assert session.device_info is None
        assert session.revoked_at is None

        public_session = session_to_public(session)
        assert public_session.id == session_id
        assert public_session.revoked_at is None

        assert result.access_token
        assert result.refresh_token
        assert result.access_token != result.refresh_token
        assert result.token_type == "bearer"
        assert result.access_token_expires_at == fixed_now + fake_token_service._access_token_ttl
        assert result.refresh_token_expires_at == fixed_now + fake_token_service._refresh_token_ttl
        assert fake_token_service.issued_account_ids == [UserId(account_id)]

        assert fake_uow.commit_called is True
        assert fake_uow.rollback_called is False
        assert fake_uow.closed is True

    async def test_stores_client_context_on_session(
            self,
            use_case: RegisterAccountHandler,
            fake_uow: FakeUnitOfWork,
            account_id: UUID,
    ) -> None:
        await use_case.execute(
            RegisterRequest(
                email="user@example.com",
                password="StrongPassword123!",
                ip="203.0.113.10",
                user_agent="Mozilla/5.0",
                device_info="Chrome on Windows",
            )
        )

        account = await fake_uow.accounts.get_by_id(UserId(account_id))
        assert account is not None
        sessions = await fake_uow.sessions.list_by_account_id(account.id)
        assert len(sessions) == 1
        assert sessions[0].ip == "203.0.113.10"
        assert sessions[0].user_agent == "Mozilla/5.0"
        assert sessions[0].device_info == "Chrome on Windows"

    async def test_rejects_registration_when_email_exists(
            self,
            use_case: RegisterAccountHandler,
            fake_uow: FakeUnitOfWork,
            fake_clock: FakeClock,
            fake_password_hasher: FakePasswordHasher,
            account_id: UUID,
    ) -> None:
        existing_account = Account.create(
            public_id=UserId(
                UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"),
            ),
            email=Email("user@example.com"),
            password_hash=fake_password_hasher.hash(
                "ExistingPassword123!",
            ),
            now=fake_clock.now(),
        )
        async with fake_uow:
            await fake_uow.accounts.add(existing_account)

        with pytest.raises(EmailAlreadyRegisteredError):
            await use_case.execute(
                RegisterRequest(
                    email="USER@example.com",
                    password="StrongPassword123!",
                )
            )

        assert await fake_uow.accounts.get_by_id(UserId(account_id)) is None
        assert await fake_uow.sessions.list_by_account_id(existing_account.id) == []
        assert fake_uow.commit_called is False
        assert fake_uow.rollback_called is True
        assert fake_uow.closed is True

    async def test_does_not_create_account_when_password_is_invalid(
            self,
            use_case: RegisterAccountHandler,
            fake_uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidPasswordError):
            await use_case.execute(
                RegisterRequest(
                    email="user@example.com",
                    password="123",
                )
            )

        assert fake_uow.commit_called is False
        assert fake_uow.rollback_called is False
        account = await fake_uow.accounts.get_by_email(
            Email("user@example.com"),
        )
        assert account is None
        assert await fake_uow.sessions.list_by_account_id(1) == []

    async def test_does_not_create_account_when_email_is_invalid(
            self,
            use_case: RegisterAccountHandler,
            fake_uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidEmailError):
            await use_case.execute(
                RegisterRequest(
                    email="not-an-email",
                    password="StrongPassword123!",
                )
            )

        assert fake_uow.commit_called is False
        assert fake_uow.rollback_called is False
        assert await fake_uow.sessions.list_by_account_id(1) == []
