from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.application.dto import IntegrationEvent
from src.application.ports.events import EventPublisher


class FileEventPublisher(EventPublisher):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    async def publish(self, event: IntegrationEvent) -> None:
        envelope = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": event.aggregate_id,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
        }
        line = json.dumps(envelope, ensure_ascii=False) + "\n"
        await asyncio.to_thread(self._append, line)

    def _append(self, line: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line)
