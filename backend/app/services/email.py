from __future__ import annotations

from email.message import EmailMessage
from uuid import UUID

import aiosmtplib
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import EmailDeliveryError
from app.db.models import CommunicationLog
from app.services.redaction import SecretRedaction, redact_secrets


class EmailService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def send(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
        job_id: UUID | None = None,
        candidate_id: UUID | None = None,
        interview_session_id: UUID | None = None,
        template: str,
        secrets_to_redact: list[SecretRedaction] | None = None,
    ) -> None:
        message = EmailMessage()
        message["From"] = self.settings.email_from
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        status = "sent"
        error: str | None = None
        try:
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user,
                password=self.settings.smtp_pass,
                start_tls=False,
            )
        except Exception as exc:
            status = "failed"
            error = str(exc)
        finally:
            self.session.add(
                CommunicationLog(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    interview_session_id=interview_session_id,
                    provider="smtp",
                    channel="email",
                    recipient=to_email,
                    subject=subject,
                    body=redact_secrets(body, secrets_to_redact),
                    status=status,
                    metadata_json={"template": template, "error": error},
                )
            )
            await self.session.commit()

        if error:
            raise EmailDeliveryError(f"SMTP email delivery failed: {error}")
