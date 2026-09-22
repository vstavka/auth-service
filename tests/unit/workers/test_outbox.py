from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.workers.outbox import _install_stop_signals, run_outbox_relay


def test_install_stop_signals_does_not_raise() -> None:
    import asyncio

    async def _run() -> None:
        stop = asyncio.Event()
        _install_stop_signals(stop)

    asyncio.run(_run())


@pytest.mark.asyncio
async def test_run_outbox_relay_invokes_run_forever(monkeypatch: pytest.MonkeyPatch) -> None:
    relay = MagicMock()
    relay.run_forever = AsyncMock()

    container = MagicMock()
    container.outbox_relay.return_value = relay

    settings = SimpleNamespace(
        logging=SimpleNamespace(level="WARNING", path=None),
        app=SimpleNamespace(name="auth-service", version="0.1.0"),
    )
    monkeypatch.setattr("src.workers.outbox.Settings", lambda: settings)
    monkeypatch.setattr("src.workers.outbox.setup_logging", lambda **kwargs: None)
    monkeypatch.setattr("src.workers.outbox.Container", lambda: container)
    monkeypatch.setattr("src.workers.outbox._install_stop_signals", lambda stop: None)

    await run_outbox_relay()

    relay.run_forever.assert_awaited_once()
