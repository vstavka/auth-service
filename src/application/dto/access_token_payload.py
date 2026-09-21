from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects import SessionId, UserId


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    account_id: UserId
    session_id: SessionId
    expires_at: datetime
