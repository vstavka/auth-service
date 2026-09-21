from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.application.dto import SessionPublic


class SessionPublicSchema(BaseModel):
    id: UUID
    ip: str | None
    user_agent: str | None
    device_info: str | None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


def session_public_to_schema(session: SessionPublic) -> SessionPublicSchema:
    return SessionPublicSchema(
        id=session.id,
        ip=session.ip,
        user_agent=session.user_agent,
        device_info=session.device_info,
        created_at=session.created_at,
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )
