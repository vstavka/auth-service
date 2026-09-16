from datetime import UTC, datetime, timedelta

from src.application.ports.system.clock import Clock


class FakeClock(Clock):
    def __init__(self, now: datetime) -> None:
        if now.tzinfo is None:
            raise ValueError("FakeClock requires timezone-aware datetime")

        self._now = now.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def set(self, value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError("FakeClock requires timezone-aware datetime")

        self._now = value.astimezone(UTC)

    def advance(self, delta: timedelta) -> None:
        self._now += delta
