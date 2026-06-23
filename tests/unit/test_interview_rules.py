from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.agents.shared.utils import is_interview_expired
from app.db.models import InterviewSession


def test_interview_expiration_check() -> None:
    session = InterviewSession(expires_at=datetime.now(UTC) - timedelta(minutes=1))

    assert is_interview_expired(session)


def test_interview_not_expired_without_expiry() -> None:
    session = InterviewSession(expires_at=None)

    assert not is_interview_expired(session)

