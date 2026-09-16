from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.commands.register_account import (
    RegisterAccount,
    RegisterAccountCommand,
)
from src.domain.entities import Account
from src.domain.enums import AccountStatus
from src.domain.exceptions.email import EmailAlreadyRegisteredError, InvalidEmailError
from src.domain.exceptions.password import InvalidPasswordError
from src.domain.services.password_policy import PasswordPolicy

from src.domain.value_objects import Email, UserId
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
    def fake_uow(self) -> FakeUnitOfWork:
        return FakeUnitOfWork()

    @pytest.fixture
    def fake_clock(self, fixed_now: datetime) -> FakeClock:
        return FakeClock(fixed_now)

    @pytest.fixture
    def fake_id_generator(self, account_id: UUID) -> FakeIdGenerator:
        return FakeIdGenerator(ids=[account_id])

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
    ) -> RegisterAccount:
        return RegisterAccount(
            uow=fake_uow,
            password_policy=PasswordPolicy(),
            password_hasher=fake_password_hasher,
            token_service=fake_token_service,
            id_generator=fake_id_generator,
            clock=fake_clock,
        )

    async def test_registers_new_account_and_returns_tokens(
        self,
        use_case: RegisterAccount,
        fake_uow: FakeUnitOfWork,
        account_id: UUID,
    ) -> None:
        result = await use_case.execute(
            RegisterAccountCommand(
                email="User@Example.COM",
                password="StrongPassword123!",
            )
        )

        account = await fake_uow.accounts.get_by_id(
            UserId(account_id),
        )

        assert account is not None
        assert account.id == UserId(account_id)
        assert account.email == Email("user@example.com")
        assert account.status is AccountStatus.ACTIVE
        assert account.password_hash.value != "StrongPassword123!"

        assert result.access_token
        assert result.refresh_token
        assert result.access_token != result.refresh_token
        assert result.token_type == "bearer"

        assert fake_uow.commit_called is True
        assert fake_uow.rollback_called is False
        assert fake_uow.closed is True

    async def test_rejects_registration_when_email_exists(
        self,
        use_case: RegisterAccount,
        fake_uow: FakeUnitOfWork,
        fake_clock: FakeClock,
        fake_password_hasher: FakePasswordHasher,
    ) -> None:
        existing_account = Account.create(
            account_id=UserId(
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
                RegisterAccountCommand(
                    email="USER@example.com",
                    password="StrongPassword123!",
                )
            )

        assert fake_uow.commit_called is False
        assert fake_uow.rollback_called is True

    async def test_does_not_create_account_when_password_is_invalid(
        self,
        use_case: RegisterAccount,
        fake_uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidPasswordError):
            await use_case.execute(
                RegisterAccountCommand(
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

    async def test_does_not_create_account_when_email_is_invalid(
        self,
        use_case: RegisterAccount,
        fake_uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidEmailError):
            await use_case.execute(
                RegisterAccountCommand(
                    email="not-an-email",
                    password="StrongPassword123!",
                )
            )

        assert fake_uow.commit_called is False
        assert fake_uow.rollback_called is False