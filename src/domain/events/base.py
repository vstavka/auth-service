from __future__ import annotations

from datetime import datetime
from typing import Protocol


class DomainEvent(Protocol):
    occurred_at: datetime

    def __str__(self):
        return f"Event:{self.occurred_at}"
