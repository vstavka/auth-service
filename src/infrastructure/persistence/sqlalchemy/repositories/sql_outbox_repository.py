from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.application.dto import IntegrationEvent
from src.application.ports.events import OutboxRepository
from src.infrastructure.persistence.sqlalchemy.mappers.outbox import (
    outbox_domain_to_orm,
    outbox_orm_to_domain,
)
from src.infrastructure.persistence.sqlalchemy.models.outbox_message import OutboxMessageModel

logger = logging.getLogger(__name__)


class SQLOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: IntegrationEvent) -> None:
        logger.debug(
            "Adding outbox event id=%s type=%s",
            event.event_id,
            event.event_type,
        )
        model = outbox_domain_to_orm(
            event,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()

    async def list_unpublished(self, limit: int) -> list[IntegrationEvent]:
        stmt = (
            select(OutboxMessageModel)
            .where(OutboxMessageModel.published_at.is_(None))
            .order_by(OutboxMessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [outbox_orm_to_domain(row) for row in result.scalars().all()]

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None:
        model = await self._get_or_raise(event_id)
        model.published_at = published_at
        model.last_error = None
        await self._session.flush()
        logger.debug("Outbox event published id=%s", event_id)

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        model = await self._get_or_raise(event_id)
        model.attempts += 1
        model.last_error = error
        await self._session.flush()
        logger.warning(
            "Outbox event publish failed id=%s attempts=%s",
            event_id,
            model.attempts,
        )

    async def _get_or_raise(self, event_id: UUID) -> OutboxMessageModel:
        stmt = select(OutboxMessageModel).where(OutboxMessageModel.id == str(event_id))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise RuntimeError(f"Outbox message id={event_id} not found")
        return model
