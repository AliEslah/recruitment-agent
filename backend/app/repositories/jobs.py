from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import Job, JobStatus
from app.schemas.jobs import JobCreate, JobCriteriaUpdate
from app.services.status_transitions import transition_job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: JobCreate) -> Job:
        job = Job(**payload.model_dump())
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def list(self) -> list[Job]:
        result = await self.session.scalars(select(Job).order_by(Job.created_at.desc()))
        return list(result)

    async def get(self, job_id: UUID) -> Job:
        job = await self.session.get(Job, job_id)
        if not job:
            raise NotFoundError("Job not found.")
        return job

    async def update_criteria(self, job_id: UUID, payload: JobCriteriaUpdate) -> Job:
        job = await self.get(job_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def approve_criteria(self, job_id: UUID) -> Job:
        job = await self.get(job_id)
        transition_job(job, JobStatus.APPROVED)
        await self.session.commit()
        await self.session.refresh(job)
        return job
