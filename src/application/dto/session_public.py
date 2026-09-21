from dataclasses import dataclass
from datetime import datetime
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
