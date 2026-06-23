from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.final_decision.graph import run_final_decision_graph
from app.api.deps import require_recruiter_user
from app.core.errors import ConflictError, ValidationAppError
from app.db.models import AuditLog, CandidateStatus, HumanDecision, HumanDecisionStage, HumanDecisionValue, User
from app.db.session import get_session
from app.repositories.candidates import CandidateRepository
from app.repositories.decisions import DecisionRepository
from app.repositories.logs import LogRepository
from app.schemas.common import HumanDecisionCreate
from app.schemas.decisions import FinalScorecardRead
from app.services.status_transitions import transition_candidate

router = APIRouter(tags=["decisions"], dependencies=[Depends(require_recruiter_user)])


@router.post("/candidates/{candidate_id}/final-scorecard", response_model=FinalScorecardRead)
async def create_final_scorecard(
    candidate_id: UUID,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> FinalScorecardRead:
    candidate = await CandidateRepository(session).get(candidate_id)
    existing = await DecisionRepository(session).latest_scorecard(candidate.id, candidate.job_id)
    if existing and not force:
        return existing
    await run_final_decision_graph({"session": session, "candidate_id": candidate.id, "job_id": candidate.job_id})
    scorecard = await DecisionRepository(session).latest_scorecard(candidate.id, candidate.job_id)
    if not scorecard:
        raise ConflictError("Final scorecard was not created.")
    await LogRepository(session).audit(
        AuditLog(
            actor_user_id=current_user.id,
            entity_type="candidate",
            entity_id=candidate.id,
            action="GENERATE_FINAL_SCORECARD",
            metadata_json={"scorecard_id": str(scorecard.id), "force": force},
        )
    )
    return scorecard


@router.get("/candidates/{candidate_id}/final-scorecard", response_model=FinalScorecardRead)
async def get_final_scorecard(candidate_id: UUID, session: AsyncSession = Depends(get_session)) -> FinalScorecardRead:
    candidate = await CandidateRepository(session).get(candidate_id)
    scorecard = await DecisionRepository(session).latest_scorecard(candidate.id, candidate.job_id)
    if not scorecard:
        raise ConflictError("Final scorecard has not been created.")
    return scorecard


@router.post("/candidates/{candidate_id}/final-decision", response_model=FinalScorecardRead | dict)
async def final_decision(
    candidate_id: UUID,
    payload: HumanDecisionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> FinalScorecardRead | dict:
    if not payload.reason.strip():
        raise ValidationAppError("Every human decision requires a reason.")
    candidate = await CandidateRepository(session).get(candidate_id)
    decision = HumanDecisionValue(payload.decision)
    if decision == HumanDecisionValue.APPROVE:
        transition_candidate(candidate, CandidateStatus.APPROVED)
    elif decision == HumanDecisionValue.REJECT:
        transition_candidate(candidate, CandidateStatus.REJECTED_FINAL)
    else:
        transition_candidate(candidate, CandidateStatus.FINAL_REVIEW)
    session.add(
        HumanDecision(
            job_id=candidate.job_id,
            candidate_id=candidate.id,
            user_id=current_user.id,
            stage=HumanDecisionStage.FINAL,
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
            action="FINAL_DECISION",
            metadata_json={"decision": decision.value, "reason": payload.reason},
        )
    )
    scorecard = await DecisionRepository(session).latest_scorecard(candidate.id, candidate.job_id)
    return scorecard or {"candidate_id": candidate.id, "status": candidate.status.value}
