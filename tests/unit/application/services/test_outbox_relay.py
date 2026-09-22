from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.dto import IntegrationEvent
from src.application.ports.events import EventPublisher
from src.application.services import OutboxRelay
from src.infrastructure.messaging import InMemoryEventPublisher
from tests.fakes.system.fake_clock import FakeClock
from tests.fakes.system.fake_unit_of_work import FakeUnitOfWork

EVENT = IntegrationEvent(
    event_id=UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
    event_type="identity.account.registered",
    aggregate_id="agg-1",
    occurred_at=datetime(2026, 9, 22, 12, 0, tzinfo=UTC),
    payload={"ok": True},
)


class FailingPublisher(EventPublisher):
    async def publish(self, event: IntegrationEvent) -> None:
        raise RuntimeError("broker down")


@pytest.mark.asyncio
class TestOutboxRelay:
    async def test_run_once_marks_published(self) -> None:
        uow = FakeUnitOfWork()
        await uow.outbox.add(EVENT)
        publisher = InMemoryEventPublisher()
        clock = FakeClock(datetime(2026, 9, 22, 13, 0, tzinfo=UTC))
        relay = OutboxRelay(
            uow=uow,
            publisher=publisher,
            clock=clock,
            batch_size=10,
            poll_interval=timedelta(seconds=1),
        )

        published = await relay.run_once()

        assert published == 1
        assert publisher.published == [EVENT]
        assert uow.outbox.published_at[EVENT.event_id] == clock.now()
        assert await uow.outbox.list_unpublished(10) == []

    async def test_run_once_marks_failed(self) -> None:
        uow = FakeUnitOfWork()
        await uow.outbox.add(EVENT)
        clock = FakeClock(datetime(2026, 9, 22, 13, 0, tzinfo=UTC))
        relay = OutboxRelay(
            uow=uow,
            publisher=FailingPublisher(),
            clock=clock,
            batch_size=10,
            poll_interval=timedelta(seconds=1),
        )

        published = await relay.run_once()

        assert published == 0
        assert EVENT.event_id not in uow.outbox.published_at
        assert uow.outbox.failures[EVENT.event_id] == (1, "broker down")
        assert await uow.outbox.list_unpublished(10) == [EVENT]

    async def test_run_forever_stops_on_event(self) -> None:
        import asyncio

        uow = FakeUnitOfWork()
        publisher = InMemoryEventPublisher()
        relay = OutboxRelay(
            uow=uow,
            publisher=publisher,
            clock=FakeClock(datetime(2026, 9, 22, 13, 0, tzinfo=UTC)),
            batch_size=10,
            poll_interval=timedelta(milliseconds=10),
        )
        stop = asyncio.Event()
        stop.set()
        await relay.run_forever(stop_event=stop)

    async def test_run_forever_publishes_then_stops(self) -> None:
        import asyncio

        uow = FakeUnitOfWork()
        await uow.outbox.add(EVENT)
        publisher = InMemoryEventPublisher()
        relay = OutboxRelay(
            uow=uow,
            publisher=publisher,
            clock=FakeClock(datetime(2026, 9, 22, 13, 0, tzinfo=UTC)),
            batch_size=10,
            poll_interval=timedelta(milliseconds=10),
        )
        stop = asyncio.Event()

        async def stopper() -> None:
            await asyncio.sleep(0.05)
            stop.set()

        await asyncio.gather(relay.run_forever(stop_event=stop), stopper())
        assert publisher.published == [EVENT]
