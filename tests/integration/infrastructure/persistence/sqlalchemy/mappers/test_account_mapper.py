from datetime import datetime, UTC
from uuid import uuid4

import pytest
from uuid6 import uuid7

from src.domain.entities.account import Account
from src.domain.enums.account_status import AccountStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.domain.value_objects.user_id import UserId
from src.infrastructure.persistence.sqlalchemy.mappers.account import (
    account_domain_to_orm,
    account_orm_to_domain,
)
from src.infrastructure.persistence.sqlalchemy.models.account import Account as AccountORM


@pytest.fixture
def domain_account() -> Account:
    now = datetime.now(UTC)
    return Account(
        public_id=UserId(uuid7()),
        id=1,
        email=Email("user@example.com"),
        password_hash=PasswordHash("hashed-value"),
        status=AccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


class TestAccountDomainToOrm:
    def test_maps_all_fields(self, domain_account: Account):
        orm_account = account_domain_to_orm(domain_account)

        assert isinstance(orm_account, AccountORM)
        assert orm_account.public_id == str(domain_account.public_id.value)
        assert orm_account.email == domain_account.email.value
        assert orm_account.password_hash == domain_account.password_hash.value
        assert orm_account.status == domain_account.status
        assert orm_account.created_at == domain_account.created_at
        assert orm_account.updated_at == domain_account.updated_at

    def test_does_not_set_internal_int_id(self, domain_account: Account):
        """
        Внутренний int id — deталь БД. Domain-сущность не должна его знать,
        и маппер не должен пытаться его проставлять при создании новой записи.
        """
        orm_account = account_domain_to_orm(domain_account)
        assert orm_account.id is None


class TestAccountOrmToDomain:
    def test_maps_all_fields(self):
        now = datetime.now(UTC)
        public_id = uuid4()
        orm_account = AccountORM(
            id=1,
            public_id=public_id,
            email="user@example.com",
            password_hash="hashed-value",
            status=AccountStatus.DISABLED,
            created_at=now,
            updated_at=now,
        )

        account = account_orm_to_domain(orm_account)

        assert isinstance(account, Account)
        assert account.id == 1
        assert account.public_id.value == public_id
        assert account.email.value == "user@example.com"
        assert account.password_hash.value == "hashed-value"
        assert account.status == AccountStatus.DISABLED
        assert account.created_at == now
        assert account.updated_at == now

    def test_status_is_enum_not_raw_string(self):
        """
        Регрессионный тест на values_callable: убеждаемся, что после round-trip
        через БД/маппер status остаётся членом AccountStatus, а не сырой строкой.
        """
        orm_account = AccountORM(
            id=1,
            public_id=uuid4(),
            email="user@example.com",
            password_hash="hashed-value",
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        account = account_orm_to_domain(orm_account)
        assert account.status is AccountStatus.ACTIVE

    def test_orm_to_domain_accepts_public_id_as_str(self):
        now = datetime.now(UTC)
        public_id = uuid4()
        orm_account = AccountORM(
            id=1,
            public_id=str(public_id),
            email="user@example.com",
            password_hash="hashed-value",
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        account = account_orm_to_domain(orm_account)

        assert account.public_id.value == public_id


class TestRoundTrip:
    def test_domain_to_orm_to_domain_preserves_data(self, domain_account: Account):
        orm_account = account_domain_to_orm(domain_account)
        restored = account_orm_to_domain(orm_account)

        assert restored.public_id.value == domain_account.public_id.value
        assert restored.email.value == domain_account.email.value
        assert restored.password_hash.value == domain_account.password_hash.value
        assert restored.status == domain_account.status
        assert restored.created_at == domain_account.created_at
        assert restored.updated_at == domain_account.updated_at