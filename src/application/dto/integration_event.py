# src/application/dto/integration_event.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IntegrationEvent:
    event_id: UUID
    event_type: str
    aggregate_id: str
    occurred_at: datetime
    payload: dict[str, Any]