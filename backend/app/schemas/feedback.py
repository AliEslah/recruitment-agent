from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import AuditLogRead, LlmCallLogRead, ORMModel


class PilotFeedbackType(str, enum.Enum):
    RECRUITER_SCORECARD_FEEDBACK = "RECRUITER_SCORECARD_FEEDBACK"
    HIRING_MANAGER_SCORECARD_FEEDBACK = "HIRING_MANAGER_SCORECARD_FEEDBACK"
    CANDIDATE_INTERVIEW_FEEDBACK = "CANDIDATE_INTERVIEW_FEEDBACK"
    BUG_REPORT = "BUG_REPORT"
    GENERAL_FEEDBACK = "GENERAL_FEEDBACK"


class PilotFeedbackCreate(BaseModel):
    candidate_id: UUID | None = None
    job_id: UUID | None = None
    interview_session_id: UUID | None = None
    feedback_type: PilotFeedbackType
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=4000)
    metadata_json: dict[str, Any] | None = None


class CandidateInterviewFeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=4000)


class PilotFeedbackRead(ORMModel):
    id: UUID
    user_id: UUID | None
    candidate_id: UUID | None
    job_id: UUID | None
    interview_session_id: UUID | None
    feedback_type: str
    rating: int
    comment: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


class PilotDashboardSummary(ORMModel):
    jobs_count: int
    candidates_count: int
    interviews_completed_count: int
    feedback_count: int
    recent_feedback: list[PilotFeedbackRead]
    recent_llm_failures: list[LlmCallLogRead]
    recent_audit_events: list[AuditLogRead]
