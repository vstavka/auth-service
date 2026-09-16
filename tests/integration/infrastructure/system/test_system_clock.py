from datetime import UTC, datetime, timedelta

from src.infrastructure.system import SystemClock


class TestSystemClock:
    def test_returns_timezone_aware_datetime(self) -> None:
        clock = SystemClock()

        now = clock.now()

        assert isinstance(now, datetime)
        assert now.tzinfo is not None
        assert now.utcoffset() == timedelta()

    def test_returns_utc_datetime(self) -> None:
        clock = SystemClock()

        now = clock.now()

        assert now.tzinfo == UTC

    def test_returns_current_time(self) -> None:
        clock = SystemClock()
        before = datetime.now(UTC)

        actual = clock.now()

        after = datetime.now(UTC)

        assert before <= actual <= after
