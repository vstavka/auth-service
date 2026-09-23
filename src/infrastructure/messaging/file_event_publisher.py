from __future__ import annotations

import asyncio
from pathlib import Path

from src.application.dto import IntegrationEvent
from src.application.ports.events import EventPublisher
from src.infrastructure.messaging.envelope import event_to_bytes


class FileEventPublisher(EventPublisher):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    async def publish(self, event: IntegrationEvent) -> None:
        line = event_to_bytes(event).decode("utf-8") + "\n"
        await asyncio.to_thread(self._append, line)

    def _append(self, line: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line)
