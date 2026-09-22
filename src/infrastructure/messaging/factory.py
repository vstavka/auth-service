from __future__ import annotations

import logging

from src.application.ports.events import EventPublisher
from src.infrastructure.messaging.file_event_publisher import FileEventPublisher
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher

logger = logging.getLogger(__name__)


def create_event_publisher(*, kind: str, file_path: str) -> EventPublisher:
    if kind == "file":
        logger.info("Using file event publisher", extra={"path": file_path})
        return FileEventPublisher(file_path)
    logger.info("Using in-memory event publisher")
    return InMemoryEventPublisher()
