from uuid import UUID

from src.domain.entities import Account
from src.domain.value_objects import UserId, Email, PasswordHash
from src.infrastructure.persistence.sqlalchemy.models import Account as AccountORM


def account_orm_to_domain(orm_account: AccountORM) -> Account:
    return Account(
        id=orm_account.id,
        public_id=UserId(
            UUID(orm_account.public_id) if not isinstance(orm_account.public_id, UUID) else orm_account.public_id),
        email=Email(orm_account.email),
        status=orm_account.status,
        password_hash=PasswordHash(orm_account.password_hash),
        created_at=orm_account.created_at,
        updated_at=orm_account.updated_at,
    )


def account_domain_to_orm(account: Account) -> AccountORM:
    return AccountORM(
        public_id=str(account.public_id.value),
        email=account.email.value,
        status=account.status,
        password_hash=account.password_hash.value,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )
