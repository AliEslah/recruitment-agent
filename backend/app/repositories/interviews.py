from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import InterviewEvaluation, InterviewMessage, InterviewSession


class InterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session(self, session_id: UUID) -> InterviewSession:
        interview = await self.session.get(InterviewSession, session_id)
        if not interview:
            raise NotFoundError("Interview session not found.")
        return interview

    async def get_by_token_hash(self, token_hash: str) -> InterviewSession:
        interview = await self.session.scalar(
            select(InterviewSession).where(InterviewSession.secure_token_hash == token_hash)
        )
        if not interview:
            raise NotFoundError("Interview token not found.")
        return interview

    async def messages(self, session_id: UUID) -> list[InterviewMessage]:
        result = await self.session.scalars(
            select(InterviewMessage)
            .where(InterviewMessage.interview_session_id == session_id)
            .order_by(InterviewMessage.created_at.asc())
        )
        return list(result)

    async def latest_evaluation(self, session_id: UUID) -> InterviewEvaluation | None:
        return await self.session.scalar(
            select(InterviewEvaluation)
            .where(InterviewEvaluation.interview_session_id == session_id)
            .order_by(InterviewEvaluation.created_at.desc())
            .limit(1)
        )

    async def latest_evaluations_for_sessions(self, session_ids: list[UUID]) -> dict[UUID, InterviewEvaluation]:
        if not session_ids:
            return {}
        result = await self.session.scalars(
            select(InterviewEvaluation)
            .where(InterviewEvaluation.interview_session_id.in_(session_ids))
            .order_by(InterviewEvaluation.interview_session_id.asc(), InterviewEvaluation.created_at.desc())
        )
        latest: dict[UUID, InterviewEvaluation] = {}
        for evaluation in result:
            latest.setdefault(evaluation.interview_session_id, evaluation)
        return latest

    async def list_for_candidate(self, candidate_id: UUID) -> list[InterviewSession]:
        result = await self.session.scalars(
            select(InterviewSession)
            .where(InterviewSession.candidate_id == candidate_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(result)

    async def list_for_job(self, job_id: UUID) -> list[InterviewSession]:
        result = await self.session.scalars(
            select(InterviewSession)
            .where(InterviewSession.job_id == job_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(result)
