from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_user
from app.db.models import AuditLog, Candidate, InterviewSession, InterviewSessionStatus, Job, LlmCallLog, PilotFeedback
from app.db.session import get_session
from app.repositories.feedback import FeedbackRepository
from app.repositories.logs import LogRepository
from app.schemas.common import AuditLogRead, CommunicationLogRead, LlmCallLogRead
from app.schemas.feedback import PilotDashboardSummary, PilotFeedbackRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_user)])


@router.get("/llm-usage", response_model=list[LlmCallLogRead])
async def llm_usage(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).llm_usage(limit)


@router.get("/audit", response_model=list[AuditLogRead])
async def audit(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).audit_logs(limit)


@router.get("/communications", response_model=list[CommunicationLogRead])
async def communications(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).communications(limit)


@router.get("/feedback", response_model=list[PilotFeedbackRead])
async def feedback(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await FeedbackRepository(session).list_recent(limit)


@router.get("/pilot-summary", response_model=PilotDashboardSummary)
async def pilot_summary(session: AsyncSession = Depends(get_session)) -> PilotDashboardSummary:
    jobs_count = await session.scalar(select(func.count()).select_from(Job))
    candidates_count = await session.scalar(select(func.count()).select_from(Candidate))
    interviews_completed_count = await session.scalar(
        select(func.count()).select_from(InterviewSession).where(InterviewSession.status == InterviewSessionStatus.COMPLETED)
    )
    feedback_count = await session.scalar(select(func.count()).select_from(PilotFeedback))
    recent_feedback = await FeedbackRepository(session).list_recent(5)
    recent_llm_failures = list(
        await session.scalars(
            select(LlmCallLog).where(LlmCallLog.status != "success").order_by(LlmCallLog.created_at.desc()).limit(5)
        )
    )
    recent_audit_events = list(await session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5)))
    return PilotDashboardSummary(
        jobs_count=jobs_count or 0,
        candidates_count=candidates_count or 0,
        interviews_completed_count=interviews_completed_count or 0,
        feedback_count=feedback_count or 0,
        recent_feedback=recent_feedback,
        recent_llm_failures=recent_llm_failures,
        recent_audit_events=recent_audit_events,
    )
