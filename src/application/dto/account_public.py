from dataclasses import dataclass
from datetime import datetime
from typing import Any
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

    def to_dict(self) -> dict[str, str]:
        return {
            "id": str(self.id),
            "email": self.email,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountPublic":
        return cls(
            id=UUID(data["id"]),
            email=data["email"],
            status=AccountStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


def account_to_public(account: Account) -> AccountPublic:
    return AccountPublic(
        id=account.public_id.value,
        email=account.email.value,
        status=account.status,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )
