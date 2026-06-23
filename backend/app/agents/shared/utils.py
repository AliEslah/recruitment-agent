from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.db.models import InterviewSession, SecurityEventType


def normalize_criteria_weights(criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not criteria:
        return criteria
    total = sum(float(item.get("weight") or 0) for item in criteria)
    if total <= 0:
        weight = round(100 / len(criteria), 2)
        return [{**item, "weight": weight} for item in criteria]
    normalized: list[dict[str, Any]] = []
    running = 0.0
    for item in criteria:
        value = round(float(item.get("weight") or 0) * 100 / total, 2)
        running += value
        normalized.append({**item, "weight": value})
    diff = round(100 - running, 2)
    normalized[-1]["weight"] = round(float(normalized[-1]["weight"]) + diff, 2)
    return normalized


def criteria_weight_total(criteria: list[dict[str, Any]]) -> float:
    return round(sum(float(item.get("weight") or 0) for item in criteria), 2)


def is_interview_expired(session: InterviewSession, now: datetime | None = None) -> bool:
    if not session.expires_at:
        return False
    current = now or datetime.now(UTC)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= current


def append_security_event(
    session: InterviewSession,
    event_type: SecurityEventType,
    metadata: dict[str, Any] | None = None,
) -> None:
    events = list(session.security_events_json or [])
    events.append(
        {
            "type": event_type.value,
            "at": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }
    )
    session.security_events_json = events

