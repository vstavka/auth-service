from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from src.application.ports.events import EventPublisher
from src.application.ports.system import Clock, UnitOfWork

logger = logging.getLogger(__name__)


class OutboxRelay:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
            publisher: EventPublisher,
            clock: Clock,
            batch_size: int,
            poll_interval: timedelta,
    ) -> None:
        self._uow = uow
        self._publisher = publisher
        self._clock = clock
        self._batch_size = batch_size
        self._poll_interval = poll_interval

    async def run_once(self) -> int:
        published = 0
        async with self._uow:
            events = await self._uow.outbox.list_unpublished(self._batch_size)
            for event in events:
                try:
                    await self._publisher.publish(event)
                    await self._uow.outbox.mark_published(
                        event.event_id,
                        self._clock.now(),
                    )
                    published += 1
                except Exception as exc:
                    logger.exception(
                        "Failed to publish outbox event",
                        extra={
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                        },
                    )
                    await self._uow.outbox.mark_failed(event.event_id, str(exc))
            await self._uow.commit()
        return published

    async def run_forever(self, stop_event: asyncio.Event | None = None) -> None:
        stop = stop_event or asyncio.Event()
        logger.info(
            "Outbox relay loop started",
            extra={
                "batch_size": self._batch_size,
                "poll_interval_seconds": self._poll_interval.total_seconds(),
            },
        )
        while not stop.is_set():
            try:
                published = await self.run_once()
                if published:
                    logger.info(
                        "Outbox relay published events",
                        extra={"count": published},
                    )
            except Exception:
                logger.exception("Outbox relay cycle failed")
            try:
                await asyncio.wait_for(
                    stop.wait(),
                    timeout=self._poll_interval.total_seconds(),
                )
            except TimeoutError:
                continue
        logger.info("Outbox relay loop stopped")
