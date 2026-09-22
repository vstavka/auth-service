from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

from src.application.dto import IntegrationEvent
from src.infrastructure.persistence.sqlalchemy.models.outbox_message import OutboxMessageModel


def outbox_domain_to_orm(
        event: IntegrationEvent,
        *,
        created_at: datetime,
) -> OutboxMessageModel:
    return OutboxMessageModel(
        id=str(event.event_id),
        event_type=event.event_type,
        aggregate_id=event.aggregate_id,
        payload=json.dumps(event.payload, ensure_ascii=False, separators=(",", ":")),
        occurred_at=event.occurred_at,
        created_at=created_at,
        published_at=None,
        attempts=0,
        last_error=None,
    )


def outbox_orm_to_domain(model: OutboxMessageModel) -> IntegrationEvent:
    occurred_at = model.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    return IntegrationEvent(
        event_id=UUID(model.id),
        event_type=model.event_type,
        aggregate_id=model.aggregate_id,
        occurred_at=occurred_at,
        payload=json.loads(model.payload),
    )
