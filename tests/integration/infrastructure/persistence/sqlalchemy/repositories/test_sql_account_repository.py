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

        assert account.id is not None
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

    @pytest.mark.asyncio
    async def test_add_duplicate_public_id_raises_email_already_registered(
            self, repository: SQLAccountRepository
    ):
        public_id = uuid7()
        first = make_account(email="first@example.com", public_id=public_id)
        second = make_account(email="second@example.com", public_id=public_id)

        await repository.add(first)

        with pytest.raises(EmailAlreadyRegisteredError):
            await repository.add(second)


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

    @pytest.mark.asyncio
    async def test_get_by_id_returns_all_persisted_fields(
            self, repository: SQLAccountRepository
    ):
        account = make_account(email="fields-id@example.com")
        await repository.add(account)

        fetched = await repository.get_by_id(account.public_id)

        assert fetched is not None
        assert fetched.status is AccountStatus.ACTIVE
        assert fetched.password_hash.value == account.password_hash.value
        assert fetched.created_at.replace(tzinfo=None) == account.created_at.replace(
            tzinfo=None
        )
        assert fetched.updated_at.replace(tzinfo=None) == account.updated_at.replace(
            tzinfo=None
        )


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

    @pytest.mark.asyncio
    async def test_get_by_email_returns_all_persisted_fields(
            self, repository: SQLAccountRepository
    ):
        account = make_account(email="fields-email@example.com")
        await repository.add(account)

        fetched = await repository.get_by_email(Email("fields-email@example.com"))

        assert fetched is not None
        assert fetched.public_id == account.public_id
        assert fetched.status is AccountStatus.ACTIVE
        assert fetched.password_hash.value == account.password_hash.value
        assert fetched.created_at.replace(tzinfo=None) == account.created_at.replace(
            tzinfo=None
        )
        assert fetched.updated_at.replace(tzinfo=None) == account.updated_at.replace(
            tzinfo=None
        )


class TestGetByInternalId:
    @pytest.mark.asyncio
    async def test_returns_account_by_internal_id(
            self, repository: SQLAccountRepository
    ):
        account = make_account(email="internal-id@example.com")
        await repository.add(account)

        fetched = await repository.get_by_internal_id(account.id)

        assert fetched is not None
        assert fetched.public_id == account.public_id

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_internal_id(
            self, repository: SQLAccountRepository
    ):
        result = await repository.get_by_internal_id(999_999)
        assert result is None


class TestSave:
    @pytest.mark.asyncio
    async def test_save_persists_email_and_password_changes(
            self, repository: SQLAccountRepository
    ):
        account = make_account(email="before@example.com")
        await repository.add(account)
        changed_at = datetime.now(UTC)
        account.change_email(email=Email("after@example.com"), now=changed_at)
        account.change_password(
            new_password_hash=PasswordHash("new-hashed-value"),
            now=changed_at,
        )

        await repository.save(account)

        fetched = await repository.get_by_id(account.public_id)
        assert fetched is not None
        assert fetched.email.value == "after@example.com"
        assert fetched.password_hash.value == "new-hashed-value"

    @pytest.mark.asyncio
    async def test_save_duplicate_email_raises_domain_error(
            self, repository: SQLAccountRepository
    ):
        first = make_account(email="taken@example.com")
        second = make_account(email="free@example.com")
        await repository.add(first)
        await repository.add(second)
        second.change_email(email=Email("taken@example.com"), now=datetime.now(UTC))

        with pytest.raises(EmailAlreadyRegisteredError):
            await repository.save(second)
