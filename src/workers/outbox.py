from __future__ import annotations

import asyncio
import logging
import signal

from src.application.services import OutboxRelay
from src.infrastructure.config.settings import Settings
from src.infrastructure.di.containers import Container
from src.infrastructure.logging.config import setup_logging

logger = logging.getLogger(__name__)


def _install_stop_signals(stop: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
    except NotImplementedError:
        signal.signal(signal.SIGINT, lambda *_: stop.set())


async def run_outbox_relay() -> None:
    settings = Settings()
    setup_logging(
        level=settings.logging.level,
        service_name=f"{settings.app.name}-outbox-relay",
        service_version=settings.app.version,
        log_path=settings.logging.path,
    )
    container = Container()
    container.config.from_pydantic(settings)

    stop = asyncio.Event()
    _install_stop_signals(stop)

    publisher = container.event_publisher()
    start = getattr(publisher, "start", None)
    if start is not None:
        await start()

    relay: OutboxRelay = container.outbox_relay()
    logger.info("Outbox relay worker started")
    try:
        await relay.run_forever(stop_event=stop)
    finally:
        stop_publisher = getattr(publisher, "stop", None)
        if stop_publisher is not None:
            await stop_publisher()
        logger.info("Outbox relay worker stopped")


def main() -> None:
    asyncio.run(run_outbox_relay())


if __name__ == "__main__":
    main()
