import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.application.ports.repositories import SessionRepository
from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId
from src.infrastructure.persistence.sqlalchemy.mappers.session import (
    session_domain_to_orm,
    session_orm_to_domain,
)
from src.infrastructure.persistence.sqlalchemy.models import Session as SessionORM

logger = logging.getLogger(__name__)


class SQLSessionRepository(SessionRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, session: Session) -> None:
        logger.debug(
            "Adding session public_id=%s account_id=%s",
            session.public_id,
            session.account_id,
        )
        session_orm = session_domain_to_orm(session)
        self._session.add(session_orm)
        await self._session.flush()
        session.id = session_orm.id
        logger.debug("Session added successfully public_id=%s", session.public_id)

    async def get_by_public_id(self, public_id: SessionId) -> Session | None:
        public_id_value = str(public_id.value)
        logger.debug("Fetching session by public_id=%s", public_id_value)
        stmt = select(SessionORM).where(SessionORM.public_id == public_id_value)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            logger.debug("Session not found public_id=%s", public_id_value)
            return None
        return session_orm_to_domain(entity)

    async def get_by_refresh_token_hash(
            self,
            token_hash: RefreshTokenHash,
    ) -> Session | None:
        logger.debug("Fetching session by refresh token hash")
        stmt = select(SessionORM).where(
            SessionORM.refresh_token_hash == token_hash.value,
        )
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            logger.debug("Session not found by refresh token hash")
            return None
        return session_orm_to_domain(entity)

    async def list_by_account_id(self, account_id: int) -> list[Session]:
        logger.debug("Listing sessions by account_id=%s", account_id)
        stmt = select(SessionORM).where(SessionORM.account_id == account_id)
        result = await self._session.execute(stmt)
        return [session_orm_to_domain(entity) for entity in result.scalars().all()]

    async def save(self, session: Session) -> None:
        """Сохраняет изменения существующей сессии."""
        if session.id is None:
            raise RuntimeError("Cannot save session without id")

        logger.debug("Saving session id=%s", session.id)
        stmt = select(SessionORM).where(SessionORM.id == session.id)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise RuntimeError(f"Session id={session.id} not found")

        entity.refresh_token_hash = session.refresh_token_hash.value
        entity.ip = session.ip
        entity.user_agent = session.user_agent
        entity.device_info = session.device_info
        entity.expires_at = session.expires_at
        entity.revoked_at = session.revoked_at
        await self._session.flush()

