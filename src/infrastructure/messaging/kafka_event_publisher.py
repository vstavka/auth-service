from __future__ import annotations

from aiokafka import AIOKafkaProducer

from src.application.dto import IntegrationEvent
from src.application.ports.events import EventPublisher
from src.infrastructure.messaging.envelope import event_to_bytes


class KafkaEventPublisher(EventPublisher):
    def __init__(
            self,
            *,
            bootstrap_servers: str,
            client_id: str,
            producer: AIOKafkaProducer | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._client_id = client_id
        self._producer = producer

    async def start(self) -> None:
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                client_id=self._client_id,
                acks="all",
            )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def publish(self, event: IntegrationEvent) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventPublisher is not started")
        await self._producer.send_and_wait(
            topic=event.event_type,
            key=event.aggregate_id.encode("utf-8"),
            value=event_to_bytes(event),
        )
