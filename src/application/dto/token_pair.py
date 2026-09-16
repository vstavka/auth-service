from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    token_type: str = "bearer"
