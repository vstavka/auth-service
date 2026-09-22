from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums import AccountStatus
from src.domain.events import DomainEvent, AccountCreated
from src.domain.value_objects import UserId, Email, PasswordHash


@dataclass(slots=True)
class Account:
    id: int | None
    public_id: UserId
    email: Email
    status: AccountStatus
    password_hash: PasswordHash
    created_at: datetime
    updated_at: datetime

    _events: list[DomainEvent] = field(
        default_factory=list,
        init=False,
        repr=False,
        compare=False,
    )

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        return tuple(self._events)

    def _record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events

    @classmethod
    def create(
            cls,
            *,
            public_id: UserId,
            email: Email,
            password_hash: PasswordHash,
            now: datetime,
            id: int = None
    ) -> "Account":
        account = cls(
            id=id,
            public_id=public_id,
            email=email,
            password_hash=password_hash,
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        account._record_event(
            AccountCreated(
                account_id=public_id,
                email=email,
                occurred_at=now,
            )
        )

        return account

    def change_password(
            self,
            *,
            new_password_hash: PasswordHash,
            now: datetime,
    ) -> None:
        self.password_hash = new_password_hash
        self.updated_at = now

    def change_email(
            self,
            *,
            email: Email,
            now: datetime,
    ) -> None:
        if self.email == email:
            return

        self.email = email
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
