import json
from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.dto import IntegrationEvent
from src.infrastructure.messaging.factory import create_event_publisher
from src.infrastructure.messaging.file_event_publisher import FileEventPublisher
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher

EVENT = IntegrationEvent(
    event_id=UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
    event_type="identity.account.registered",
    aggregate_id="018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c",
    occurred_at=datetime(2026, 9, 22, 12, 0, tzinfo=UTC),
    payload={"account_id": "018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"},
)


@pytest.mark.asyncio
async def test_in_memory_publisher_appends_events() -> None:
    publisher = InMemoryEventPublisher()
    await publisher.publish(EVENT)
    assert publisher.published == [EVENT]


@pytest.mark.asyncio
async def test_file_publisher_writes_jsonl(tmp_path) -> None:
    path = tmp_path / "nested" / "events.jsonl"
    publisher = FileEventPublisher(path)
    await publisher.publish(EVENT)
    await publisher.publish(EVENT)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["event_id"] == str(EVENT.event_id)
    assert payload["event_type"] == EVENT.event_type
    assert payload["aggregate_id"] == EVENT.aggregate_id
    assert payload["payload"] == EVENT.payload


def test_create_event_publisher_memory() -> None:
    publisher = create_event_publisher(kind="memory", file_path="events.jsonl")
    assert isinstance(publisher, InMemoryEventPublisher)


def test_create_event_publisher_file(tmp_path) -> None:
    publisher = create_event_publisher(kind="file", file_path=str(tmp_path / "e.jsonl"))
    assert isinstance(publisher, FileEventPublisher)
