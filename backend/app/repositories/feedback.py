from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PilotFeedback


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, feedback: PilotFeedback) -> PilotFeedback:
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback

    async def list_recent(self, limit: int = 100) -> list[PilotFeedback]:
        result = await self.session.scalars(select(PilotFeedback).order_by(PilotFeedback.created_at.desc()).limit(limit))
        return list(result)
