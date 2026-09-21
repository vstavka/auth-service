from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import AccountStatus
from src.domain.value_objects import UserId, Email, PasswordHash


@dataclass(slots=True)
class Account:
    id: int|None
    public_id: UserId
    email: Email
    status: AccountStatus
    password_hash: PasswordHash
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
            cls,
            *,
            public_id: UserId,
            email: Email,
            password_hash: PasswordHash,
            now: datetime,
            id:int = None
    ) -> "Account":
        return cls(
            id=id,
            public_id=public_id,
            email=email,
            password_hash=password_hash,
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def change_password(
            self,
            *,
            new_password_hash: PasswordHash,
            now: datetime,
    ) -> None:
        self.password_hash = new_password_hash
        self.updated_at = now

    def disable(self, now: datetime) -> None:
        if self.status is AccountStatus.DISABLED:
            return

        self.status = AccountStatus.DISABLED
        self.updated_at = now

    def enable(self, now: datetime) -> None:
        if self.status is not AccountStatus.DISABLED:
            return

        self.status = AccountStatus.ACTIVE
        self.updated_at = now

    @property
    def is_active(self) -> bool:
        return self.status is AccountStatus.ACTIVE
