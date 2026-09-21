from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.entities import Account
from src.domain.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class AccountPublic:
    id: UUID
    email: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime


def account_to_public(account: Account) -> AccountPublic:
    return AccountPublic(
        id=account.public_id.value,
        email=account.email.value,
        status=account.status,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )
