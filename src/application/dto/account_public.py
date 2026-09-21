from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class AccountPublic:
    id: UUID
    email: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
