from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects import RefreshTokenHash, SessionId


@dataclass(slots=True)
class Session:
    id: int | None
    public_id: SessionId
    account_id: int
    refresh_token_hash: RefreshTokenHash
    ip: str | None
    user_agent: str | None
    device_info: str | None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    @classmethod
    def create(
            cls,
            *,
            public_id: SessionId,
            account_id: int,
            refresh_token_hash: RefreshTokenHash,
            now: datetime,
            expires_at: datetime,
            ip: str | None = None,
            user_agent: str | None = None,
            device_info: str | None = None,
            id: int | None = None,
    ) -> "Session":
        if expires_at <= now:
            raise ValueError("expires_at must be greater than created_at")

        return cls(
            id=id,
            public_id=public_id,
            account_id=account_id,
            refresh_token_hash=refresh_token_hash,
            ip=ip,
            user_agent=user_agent,
            device_info=device_info,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
        )

    def revoke(self, now: datetime) -> None:
        if self.revoked_at is not None:
            return

        self.revoked_at = now

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_active(self, now: datetime) -> bool:
        return not self.is_revoked and not self.is_expired(now)

    def rotate_refresh_token(
            self,
            *,
            refresh_token_hash: RefreshTokenHash,
            expires_at: datetime,
            now: datetime,
    ) -> None:
        if expires_at <= now:
            raise ValueError("expires_at must be greater than now")

        self.refresh_token_hash = refresh_token_hash
        self.expires_at = expires_at
