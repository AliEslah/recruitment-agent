from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FinalScorecard, HumanDecision


class DecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def latest_scorecard(self, candidate_id: UUID, job_id: UUID) -> FinalScorecard | None:
        return await self.session.scalar(
            select(FinalScorecard)
            .where(FinalScorecard.candidate_id == candidate_id, FinalScorecard.job_id == job_id)
            .order_by(FinalScorecard.created_at.desc())
            .limit(1)
        )

    async def create_human_decision(self, decision: HumanDecision) -> HumanDecision:
        self.session.add(decision)
        await self.session.commit()
        await self.session.refresh(decision)
        return decision

