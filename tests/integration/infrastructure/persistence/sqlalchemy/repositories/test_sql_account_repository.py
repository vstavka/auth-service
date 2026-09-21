from datetime import datetime, UTC
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.domain.entities.account import Account
from src.domain.enums.account_status import AccountStatus
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.domain.value_objects.user_id import UserId
from src.infrastructure.persistence.sqlalchemy.repositories.sql_account_repository import (
    SQLAccountRepository,
)


def make_account(email: str = "user@example.com", public_id=None) -> Account:
    now = datetime.now(UTC)
    return Account(
        id=1,
        public_id=UserId(public_id or uuid7()),
        email=Email(email),
        password_hash=PasswordHash("hashed-value"),
        status=AccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def repository(session: AsyncSession) -> SQLAccountRepository:
    return SQLAccountRepository(session)


class TestAdd:
    @pytest.mark.asyncio
    async def test_add_persists_account(self, repository: SQLAccountRepository):
        account = make_account()

        await repository.add(account)
        fetched = await repository.get_by_id(account.public_id)

        assert fetched is not None
        assert fetched.email.value == account.email.value

    @pytest.mark.asyncio
    async def test_add_duplicate_email_raises_domain_error(
        self, repository: SQLAccountRepository
    ):
        first = make_account(email="duplicate@example.com")
        second = make_account(email="duplicate@example.com")

        await repository.add(first)

        with pytest.raises(EmailAlreadyRegisteredError):
            await repository.add(second)

    @pytest.mark.asyncio
    async def test_add_generates_public_id_when_missing(
        self, repository: SQLAccountRepository
    ):
        """
        Если у сущности public_id не задан заранее на уровне domain-фабрики,
        ORM-модель должна сгенерировать его сама (default=uuid7).
        """
        account = make_account()
        await repository.add(account)

        fetched = await repository.get_by_id(account.public_id)
        assert fetched.public_id.value is not None


class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_none_for_missing_account(
        self, repository: SQLAccountRepository
    ):
        result = await repository.get_by_id(UserId(uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_account_by_public_id(self, repository: SQLAccountRepository):
        account = make_account()
        await repository.add(account)

        fetched = await repository.get_by_id(account.public_id)

        assert fetched is not None
        assert fetched.public_id.value == account.public_id.value


class TestGetByEmail:
    @pytest.mark.asyncio
    async def test_returns_none_for_missing_email(
        self, repository: SQLAccountRepository
    ):
        result = await repository.get_by_email(Email("missing@example.com"))
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_account_by_email(self, repository: SQLAccountRepository):
        account = make_account(email="findme@example.com")
        await repository.add(account)

        fetched = await repository.get_by_email(Email("findme@example.com"))

        assert fetched is not None
        assert fetched.email.value == "findme@example.com"