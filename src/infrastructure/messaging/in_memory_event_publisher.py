from __future__ import annotations

from src.application.dto import IntegrationEvent
from src.application.ports.events import EventPublisher


class InMemoryEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.published: list[IntegrationEvent] = []

    async def publish(self, event: IntegrationEvent) -> None:
        self.published.append(event)
