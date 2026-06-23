from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_calibration.graph import run_job_calibration_graph
from app.api.deps import require_recruiter_user
from app.db.models import AuditLog, User
from app.db.session import get_session
from app.repositories.jobs import JobRepository
from app.repositories.logs import LogRepository
from app.schemas.jobs import JobCreate, JobCriteriaUpdate, JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_recruiter_user)])


@router.post("", response_model=JobRead)
async def create_job(
    payload: JobCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> JobRead:
    return await JobRepository(session).create(payload.model_copy(update={"created_by_id": current_user.id}))


@router.get("", response_model=list[JobRead])
async def list_jobs(session: AsyncSession = Depends(get_session)) -> list[JobRead]:
    return await JobRepository(session).list()


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobRead:
    return await JobRepository(session).get(job_id)


@router.post("/{job_id}/calibrate", response_model=JobRead)
async def calibrate_job(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobRead:
    await run_job_calibration_graph({"session": session, "job_id": job_id})
    return await JobRepository(session).get(job_id)


@router.patch("/{job_id}/criteria", response_model=JobRead)
async def update_job_criteria(
    job_id: UUID,
    payload: JobCriteriaUpdate,
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    return await JobRepository(session).update_criteria(job_id, payload)


@router.post("/{job_id}/approve-criteria", response_model=JobRead)
async def approve_job_criteria(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> JobRead:
    job = await JobRepository(session).approve_criteria(job_id)
    await LogRepository(session).audit(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="job",
            entity_id=job.id,
            action="APPROVE_CRITERIA",
            metadata_json={"status": job.status.value},
        )
    )
    return job
