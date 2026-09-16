from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    account_id: UserId
    expires_at: datetime