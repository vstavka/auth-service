from datetime import datetime
from uuid import UUID

from src.application.dto import IntegrationEvent
from src.application.ports.events import OutboxRepository


class FakeOutboxRepository(OutboxRepository):
    def __init__(self) -> None:
        self.events: list[IntegrationEvent] = []
        self.published_at: dict[UUID, datetime] = {}
        self.failures: dict[UUID, tuple[int, str]] = {}

    async def add(self, event: IntegrationEvent) -> None:
        self.events.append(event)

    async def list_unpublished(self, limit: int) -> list[IntegrationEvent]:
        unpublished = [
            event for event in self.events if event.event_id not in self.published_at
        ]
        return unpublished[:limit]

    async def mark_published(self, event_id: UUID, published_at: datetime) -> None:
        self.published_at[event_id] = published_at
        self.failures.pop(event_id, None)

    async def mark_failed(self, event_id: UUID, error: str) -> None:
        attempts, _ = self.failures.get(event_id, (0, ""))
        self.failures[event_id] = (attempts + 1, error)
