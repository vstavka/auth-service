from __future__ import annotations

import logging
from collections.abc import Mapping

from src.application.ports.events import EventPublisher
from src.infrastructure.config.settings import EventsSettings
from src.infrastructure.messaging.file_event_publisher import FileEventPublisher
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.messaging.kafka_event_publisher import KafkaEventPublisher

logger = logging.getLogger(__name__)


def _as_events_settings(events: EventsSettings | Mapping[str, object]) -> EventsSettings:
    if isinstance(events, EventsSettings):
        return events
    return EventsSettings(_env_file=None, **dict(events))


def create_event_publisher(*, events: EventsSettings | Mapping[str, object]) -> EventPublisher:
    settings = _as_events_settings(events)
    if settings.publisher == "file":
        logger.info("Using file event publisher", extra={"path": settings.file_path})
        return FileEventPublisher(settings.file_path)
    if settings.publisher == "kafka":
        logger.info(
            "Using Kafka event publisher",
            extra={"bootstrap_servers": settings.kafka_bootstrap_servers},
        )
        return KafkaEventPublisher(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
        )
    logger.info("Using in-memory event publisher")
    return InMemoryEventPublisher()
