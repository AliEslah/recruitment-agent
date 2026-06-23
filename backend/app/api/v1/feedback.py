from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_recruiter_user
from app.db.models import PilotFeedback, User
from app.db.session import get_session
from app.repositories.feedback import FeedbackRepository
from app.schemas.feedback import PilotFeedbackCreate, PilotFeedbackRead

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=PilotFeedbackRead)
async def create_feedback(
    payload: PilotFeedbackCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_recruiter_user),
) -> PilotFeedbackRead:
    feedback = PilotFeedback(
        user_id=current_user.id,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        interview_session_id=payload.interview_session_id,
        feedback_type=payload.feedback_type.value,
        rating=payload.rating,
        comment=payload.comment,
        metadata_json=payload.metadata_json,
    )
    return await FeedbackRepository(session).create(feedback)
