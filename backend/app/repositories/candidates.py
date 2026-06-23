from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import Candidate, CandidateScore, CandidateStatus
from app.schemas.candidates import CandidateCreate
from app.services.status_transitions import transition_candidate


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job_id: UUID, payload: CandidateCreate) -> Candidate:
        candidate = Candidate(job_id=job_id, **payload.model_dump())
        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def list_for_job(self, job_id: UUID) -> list[Candidate]:
        result = await self.session.scalars(
            select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.created_at.desc())
        )
        return list(result)

    async def get(self, candidate_id: UUID) -> Candidate:
        candidate = await self.session.get(Candidate, candidate_id)
        if not candidate:
            raise NotFoundError("Candidate not found.")
        return candidate

    async def set_resume(self, candidate_id: UUID, file_path: str, resume_hash: str) -> Candidate:
        candidate = await self.get(candidate_id)
        candidate.resume_file_path = file_path
        candidate.resume_hash = resume_hash
        transition_candidate(candidate, CandidateStatus.UPLOADED)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate

    async def latest_score(self, candidate_id: UUID, job_id: UUID) -> CandidateScore | None:
        return await self.session.scalar(
            select(CandidateScore)
            .where(CandidateScore.candidate_id == candidate_id, CandidateScore.job_id == job_id)
            .order_by(CandidateScore.created_at.desc())
            .limit(1)
        )

    async def latest_scores_for_job(self, job_id: UUID) -> dict[UUID, CandidateScore]:
        result = await self.session.scalars(
            select(CandidateScore)
            .where(CandidateScore.job_id == job_id)
            .order_by(CandidateScore.candidate_id.asc(), CandidateScore.created_at.desc())
        )
        latest: dict[UUID, CandidateScore] = {}
        for score in result:
            latest.setdefault(score.candidate_id, score)
        return latest

    async def shortlist(self, candidate_id: UUID, approved: bool) -> Candidate:
        candidate = await self.get(candidate_id)
        transition_candidate(candidate, CandidateStatus.SHORTLISTED if approved else CandidateStatus.REJECTED)
        await self.session.commit()
        await self.session.refresh(candidate)
        return candidate
