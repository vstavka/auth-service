from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.events.base import DomainEvent
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class AccountCreated(DomainEvent):
    account_id: UserId
    email: Email
    occurred_at: datetime
