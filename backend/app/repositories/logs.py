from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, CommunicationLog, LlmCallLog


class LogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def llm_usage(self, limit: int = 100) -> list[LlmCallLog]:
        result = await self.session.scalars(select(LlmCallLog).order_by(LlmCallLog.created_at.desc()).limit(limit))
        return list(result)

    async def audit_logs(self, limit: int = 100) -> list[AuditLog]:
        result = await self.session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
        return list(result)

    async def communications(self, limit: int = 100) -> list[CommunicationLog]:
        result = await self.session.scalars(
            select(CommunicationLog).order_by(CommunicationLog.created_at.desc()).limit(limit)
        )
        return list(result)

    async def audit(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

