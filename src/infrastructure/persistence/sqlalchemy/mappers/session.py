from datetime import UTC, datetime
from uuid import UUID

from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId
from src.infrastructure.persistence.sqlalchemy.models import Session as SessionORM


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_utc_optional(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


def session_orm_to_domain(orm_session: SessionORM) -> Session:
    public_id = (
        UUID(orm_session.public_id)
        if not isinstance(orm_session.public_id, UUID)
        else orm_session.public_id
    )
    return Session(
        id=orm_session.id,
        public_id=SessionId(public_id),
        account_id=orm_session.account_id,
        refresh_token_hash=RefreshTokenHash(orm_session.refresh_token_hash),
        ip=orm_session.ip,
        user_agent=orm_session.user_agent,
        device_info=orm_session.device_info,
        created_at=_as_utc(orm_session.created_at),
        expires_at=_as_utc(orm_session.expires_at),
        revoked_at=_as_utc_optional(orm_session.revoked_at),
    )


def session_domain_to_orm(session: Session) -> SessionORM:
    return SessionORM(
        public_id=str(session.public_id.value),
        account_id=session.account_id,
        refresh_token_hash=session.refresh_token_hash.value,
        ip=session.ip,
        user_agent=session.user_agent,
        device_info=session.device_info,
        created_at=session.created_at,
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )
