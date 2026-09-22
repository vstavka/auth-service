from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import IntegrationEvent
from src.infrastructure.persistence.sqlalchemy.repositories.sql_outbox_repository import (
    SQLOutboxRepository,
)


def make_event() -> IntegrationEvent:
    return IntegrationEvent(
        event_id=uuid4(),
        event_type="identity.account.registered",
        aggregate_id="agg-1",
        occurred_at=datetime(2026, 9, 22, 12, 0, tzinfo=UTC),
        payload={"account_id": "agg-1", "email": "user@example.com"},
    )


@pytest.fixture
def repository(session: AsyncSession) -> SQLOutboxRepository:
    return SQLOutboxRepository(session)


@pytest.mark.asyncio
class TestSQLOutboxRepository:
    async def test_add_and_list_unpublished(self, repository: SQLOutboxRepository) -> None:
        event = make_event()
        await repository.add(event)

        unpublished = await repository.list_unpublished(10)

        assert len(unpublished) == 1
        stored = unpublished[0]
        assert stored.event_id == event.event_id
        assert stored.event_type == event.event_type
        assert stored.aggregate_id == event.aggregate_id
        assert stored.payload == event.payload

    async def test_list_unpublished_respects_limit(self, repository: SQLOutboxRepository) -> None:
        await repository.add(make_event())
        await repository.add(make_event())

        unpublished = await repository.list_unpublished(1)
        assert len(unpublished) == 1

    async def test_mark_published_excludes_from_unpublished(
            self,
            repository: SQLOutboxRepository,
    ) -> None:
        event = make_event()
        await repository.add(event)
        await repository.mark_published(event.event_id, datetime.now(UTC))

        assert await repository.list_unpublished(10) == []

    async def test_mark_failed_keeps_unpublished(
            self,
            repository: SQLOutboxRepository,
    ) -> None:
        event = make_event()
        await repository.add(event)
        await repository.mark_failed(event.event_id, "broker down")
        await repository.mark_failed(event.event_id, "still down")

        unpublished = await repository.list_unpublished(10)
        assert len(unpublished) == 1
        assert unpublished[0].event_id == event.event_id

    async def test_mark_published_missing_raises(self, repository: SQLOutboxRepository) -> None:
        with pytest.raises(RuntimeError):
            await repository.mark_published(uuid4(), datetime.now(UTC))
