from __future__ import annotations

from typing import Protocol

from src.application.dto import IntegrationEvent


class EventPublisher(Protocol):
    async def publish(self, event: IntegrationEvent) -> None:
        ...
