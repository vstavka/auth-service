from __future__ import annotations

import json

from src.application.dto import IntegrationEvent


def event_to_envelope(event: IntegrationEvent) -> dict[str, object]:
    return {
        "event_id": str(event.event_id),
        "event_type": event.event_type,
        "aggregate_id": event.aggregate_id,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": event.payload,
    }


def event_to_bytes(event: IntegrationEvent) -> bytes:
    return json.dumps(event_to_envelope(event), ensure_ascii=False).encode("utf-8")
