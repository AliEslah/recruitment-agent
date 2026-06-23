from __future__ import annotations

import csv
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.candidate_processing.graph import run_candidate_processing_graph
from app.api.deps import require_recruiter_user
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import AuditLog, CandidateStatus, HumanDecision, HumanDecisionStage, HumanDecisionValue, User
from app.db.session import get_session
from app.repositories.candidates import CandidateRepository
from app.repositories.jobs import JobRepository
from app.repositories.logs import LogRepository
from app.schemas.candidates import (
    CandidateCreate,
    CandidateListRead,
    CandidateProcessRequest,
    CandidateRead,
    CandidateScoreRead,
    CandidateScoreSummaryRead,
)
from app.schemas.common import HumanDecisionCreate
from app.services.files import save_resume_upload
from app.services.status_transitions import transition_candidate

router = APIRouter(tags=["candidates"], dependencies=[Depends(require_recruiter_user)])


def _candidate_list_read(candidate, latest_score) -> CandidateListRead:
    data = CandidateRead.model_validate(candidate).model_dump()
    score_summary = CandidateScoreSummaryRead.model_validate(latest_score) if latest_score else None
    return CandidateListRead(**data, latest_score=score_summary)


@router.post("/jobs/{job_id}/candidates", response_model=CandidateRead)
async def create_candidate(
    job_id: UUID,
    payload: CandidateCreate,
    session: AsyncSession = Depends(get_session),
) -> CandidateRead:
    await JobRepository(session).get(job_id)
    return await CandidateRepository(session).create(job_id, payload)


@router.post("/jobs/{job_id}/candidates/upload-resume", response_model=CandidateRead)
async def upload_resume(
    job_id: UUID,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    email: EmailStr | None = Form(default=None),
    phone: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> CandidateRead:
    await JobRepository(session).get(job_id)
    candidate = await CandidateRepository(session).create(job_id, CandidateCreate(name=name, email=email, phone=phone))
    path, digest = await save_resume_upload(job_id, candidate.id, file)
    return await CandidateRepository(session).set_resume(candidate.id, path, digest)


@router.post("/jobs/{job_id}/candidates/import-csv", response_model=list[CandidateRead])
async def import_candidates_csv(
    job_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> list[CandidateRead]:
    await JobRepository(session).get(job_id)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content))
    candidates = []
    for row in reader:
        candidates.append(
            await CandidateRepository(session).create(
                job_id,
                CandidateCreate(name=row.get("name"), email=row.get("email") or None, phone=row.get("phone") or None),
            )
        )
    return candidates


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateListRead])
async def list_candidates(job_id: UUID, session: AsyncSession = Depends(get_session)) -> list[CandidateListRead]:
    await JobRepository(session).get(job_id)
    candidate_repo = CandidateRepository(session)
    candidates = await candidate_repo.list_for_job(job_id)
    latest_scores = await candidate_repo.latest_scores_for_job(job_id)
    return [_candidate_list_read(candidate, latest_scores.get(candidate.id)) for candidate in candidates]


@router.get("/candidates/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: UUID, session: AsyncSession = Depends(get_session)) -> CandidateRead:
    return await CandidateRepository(session).get(candidate_id)


@router.get("/candidates/{candidate_id}/score/latest", response_model=CandidateScoreRead)
async def get_latest_candidate_score(
    candidate_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> CandidateScoreRead:
    candidate_repo = CandidateRepository(session)
    candidate = await candidate_repo.get(candidate_id)
    score = await candidate_repo.latest_score(candidate.id, candidate.job_id)
    if not score:
        raise ConflictError("Candidate score has not been created.")
    return score


@router.post("/candidates/{candidate_id}/process", response_model=CandidateScoreRead | CandidateRead)
async def process_candidate(
    candidate_id: UUID,
    payload: CandidateProcessRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> CandidateScoreRead | CandidateRead:
    candidate = await CandidateRepository(session).get(candidate_id)
    await run_candidate_processing_graph(
        {"session": session, "candidate_id": candidate.id, "job_id": candidate.job_id, "force": bool(payload and payload.force)}
    )
    score = await CandidateRepository(session).latest_score(candidate.id, candidate.job_id)
    return score or await CandidateRepository(session).get(candidate.id)


@router.get("/jobs/{job_id}/shortlist", response_model=list[CandidateRead])
async def get_shortlist(job_id: UUID, session: AsyncSession = Depends(get_session)) -> list[CandidateRead]:
    candidates = await CandidateRepository(session).list_for_job(job_id)
    return [
        candidate
        for candidate in candidates
        if candidate.status
        in {
            CandidateStatus.SCORED,
            CandidateStatus.NEEDS_REVIEW,
            CandidateStatus.SHORTLISTED,
            CandidateStatus.REJECTED,
        }
    ]


@router.post("/candidates/{candidate_id}/shortlist-decision", response_model=CandidateRead)
async def shortlist_decision(
    candidate_id: UUID,
    payload: HumanDecisionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> CandidateRead:
    if not payload.reason.strip():
        raise ValidationAppError("Every human decision requires a reason.")
    candidate = await CandidateRepository(session).get(candidate_id)
    decision = HumanDecisionValue(payload.decision)
    if decision == HumanDecisionValue.APPROVE:
        transition_candidate(candidate, CandidateStatus.SHORTLISTED)
    elif decision == HumanDecisionValue.REJECT:
        transition_candidate(candidate, CandidateStatus.REJECTED)
    else:
        transition_candidate(candidate, CandidateStatus.NEEDS_REVIEW)
    session.add(
        HumanDecision(
            job_id=candidate.job_id,
            candidate_id=candidate.id,
            user_id=current_user.id,
            stage=HumanDecisionStage.SHORTLIST,
            decision=decision,
            reason=payload.reason,
            comment=payload.comment,
        )
    )
    await session.commit()
    await LogRepository(session).audit(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="candidate",
            entity_id=candidate.id,
            action="SHORTLIST_DECISION",
            metadata_json={"decision": decision.value, "reason": payload.reason},
        )
    )
    await session.refresh(candidate)
    return candidate
