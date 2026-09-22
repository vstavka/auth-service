from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.entities import Session


@dataclass(frozen=True, slots=True)
class SessionPublic:
    id: UUID
    ip: str | None
    user_agent: str | None
    device_info: str | None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "id": str(self.id),
            "ip": self.ip,
            "user_agent": self.user_agent,
            "device_info": self.device_info,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": (
                self.revoked_at.isoformat()
                if self.revoked_at is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionPublic":
        return cls(
            id=UUID(data["id"]),
            ip=data["ip"],
            user_agent=data["user_agent"],
            device_info=data["device_info"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            revoked_at=(
                datetime.fromisoformat(data["revoked_at"])
                if data["revoked_at"] is not None
                else None
            ),
        )


def session_to_public(session: Session) -> SessionPublic:
    return SessionPublic(
        id=session.public_id.value,
        ip=session.ip,
        user_agent=session.user_agent,
        device_info=session.device_info,
        created_at=session.created_at,
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )
