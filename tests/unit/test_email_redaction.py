from __future__ import annotations

from uuid import uuid4

import pytest

from app.db.models import CommunicationLog
from app.services.email import EmailService
from app.services.redaction import SecretRedaction, redact_secrets


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        return None


def test_redact_secrets_ignores_empty_values() -> None:
    assert redact_secrets("abc", [SecretRedaction(None, "[X]"), SecretRedaction("", "[Y]")]) == "abc"


@pytest.mark.asyncio
async def test_invite_email_delivers_token_but_persists_redacted_body(monkeypatch: pytest.MonkeyPatch) -> None:
    delivered = {}

    async def fake_send(message, **kwargs):
        delivered["body"] = message.get_content()

    monkeypatch.setattr("app.services.email.aiosmtplib.send", fake_send)
    session = FakeSession()
    raw_token = "raw-token-value"
    body = f"Open this secure interview link: http://localhost/interview-entry/{raw_token}"

    await EmailService(session).send(
        to_email="candidate@example.com",
        subject="Your interview invitation",
        body=body,
        job_id=uuid4(),
        candidate_id=uuid4(),
        interview_session_id=uuid4(),
        template="interview_invitation",
        secrets_to_redact=[SecretRedaction(raw_token, "[REDACTED_INTERVIEW_TOKEN]")],
    )

    log = next(item for item in session.added if isinstance(item, CommunicationLog))
    assert raw_token in delivered["body"]
    assert raw_token not in log.body
    assert "[REDACTED_INTERVIEW_TOKEN]" in log.body
    assert raw_token not in str(log.metadata_json)


@pytest.mark.asyncio
async def test_otp_email_delivers_otp_but_persists_redacted_body(monkeypatch: pytest.MonkeyPatch) -> None:
    delivered = {}

    async def fake_send(message, **kwargs):
        delivered["body"] = message.get_content()

    monkeypatch.setattr("app.services.email.aiosmtplib.send", fake_send)
    session = FakeSession()
    otp = "123456"
    body = f"Your interview OTP is {otp}. It expires in 10 minutes."

    await EmailService(session).send(
        to_email="candidate@example.com",
        subject="Your interview OTP",
        body=body,
        job_id=uuid4(),
        candidate_id=uuid4(),
        interview_session_id=uuid4(),
        template="otp",
        secrets_to_redact=[SecretRedaction(otp, "[REDACTED_OTP]")],
    )

    log = next(item for item in session.added if isinstance(item, CommunicationLog))
    assert otp in delivered["body"]
    assert otp not in log.body
    assert "[REDACTED_OTP]" in log.body
    assert otp not in str(log.metadata_json)
