import json
from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.application.dto import IntegrationEvent
from src.infrastructure.config.settings import EventsSettings
from src.infrastructure.messaging.envelope import event_to_bytes, event_to_envelope
from src.infrastructure.messaging.factory import create_event_publisher
from src.infrastructure.messaging.file_event_publisher import FileEventPublisher
from src.infrastructure.messaging.in_memory_event_publisher import InMemoryEventPublisher
from src.infrastructure.messaging.kafka_event_publisher import KafkaEventPublisher

EVENT = IntegrationEvent(
    event_id=UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
    event_type="identity.account.registered",
    aggregate_id="018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c",
    occurred_at=datetime(2026, 9, 22, 12, 0, tzinfo=UTC),
    payload={"account_id": "018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"},
)


def _events(**overrides: object) -> EventsSettings:
    return EventsSettings(_env_file=None, **overrides)


class FakeKafkaProducer:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.sent: list[tuple[str, bytes, bytes]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send_and_wait(self, topic: str, key: bytes, value: bytes) -> None:
        self.sent.append((topic, key, value))


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
    assert payload == event_to_envelope(EVENT)


@pytest.mark.asyncio
async def test_kafka_publisher_sends_envelope_to_event_type_topic() -> None:
    producer = FakeKafkaProducer()
    publisher = KafkaEventPublisher(
        bootstrap_servers="localhost:9092",
        client_id="test",
        producer=producer,  # type: ignore[arg-type]
    )
    await publisher.start()
    await publisher.publish(EVENT)
    await publisher.stop()

    assert producer.started is True
    assert producer.stopped is True
    assert len(producer.sent) == 1
    topic, key, value = producer.sent[0]
    assert topic == EVENT.event_type
    assert key == EVENT.aggregate_id.encode("utf-8")
    assert json.loads(value) == event_to_envelope(EVENT)


@pytest.mark.asyncio
async def test_kafka_publisher_start_creates_producer(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, object] = {}

    class FakeCtor:
        def __init__(self, **kwargs: object) -> None:
            created.update(kwargs)

        async def start(self) -> None:
            created["started"] = True

        async def stop(self) -> None:
            created["stopped"] = True

    monkeypatch.setattr(
        "src.infrastructure.messaging.kafka_event_publisher.AIOKafkaProducer",
        FakeCtor,
    )
    publisher = KafkaEventPublisher(bootstrap_servers="kafka:9092", client_id="cid")
    await publisher.start()
    await publisher.stop()

    assert created["bootstrap_servers"] == "kafka:9092"
    assert created["client_id"] == "cid"
    assert created["acks"] == "all"
    assert created["started"] is True
    assert created["stopped"] is True


@pytest.mark.asyncio
async def test_kafka_publisher_publish_before_start_raises() -> None:
    publisher = KafkaEventPublisher(
        bootstrap_servers="localhost:9092",
        client_id="test",
    )
    with pytest.raises(RuntimeError, match="not started"):
        await publisher.publish(EVENT)


def test_event_to_bytes_is_json_envelope() -> None:
    payload = json.loads(event_to_bytes(EVENT))
    assert payload["event_id"] == str(EVENT.event_id)
    assert payload["event_type"] == EVENT.event_type


def test_create_event_publisher_memory() -> None:
    publisher = create_event_publisher(events=_events(publisher="memory"))
    assert isinstance(publisher, InMemoryEventPublisher)


def test_create_event_publisher_file(tmp_path) -> None:
    publisher = create_event_publisher(
        events=_events(publisher="file", file_path=str(tmp_path / "e.jsonl")),
    )
    assert isinstance(publisher, FileEventPublisher)


def test_create_event_publisher_kafka() -> None:
    publisher = create_event_publisher(events=_events(publisher="kafka"))
    assert isinstance(publisher, KafkaEventPublisher)


def test_create_event_publisher_accepts_mapping() -> None:
    publisher = create_event_publisher(events={"publisher": "memory"})
    assert isinstance(publisher, InMemoryEventPublisher)
