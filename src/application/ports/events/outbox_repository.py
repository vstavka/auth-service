from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.application.dto import IntegrationEvent


class OutboxRepository(Protocol):
    async def add(self, event: IntegrationEvent) -> None:
        ...

    async def list_unpublished(self, limit: int) -> list[IntegrationEvent]:
        ...

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None:
        ...

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        ...
