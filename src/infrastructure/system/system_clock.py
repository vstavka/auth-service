from datetime import datetime, timezone

from src.application.ports.system import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        """Возвращает текущий момент времени в UTC."""
        return datetime.now(timezone.utc)
