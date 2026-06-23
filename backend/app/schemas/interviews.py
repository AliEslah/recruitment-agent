from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import InterviewMode, InterviewSessionStatus
from app.schemas.common import ORMModel


class InterviewSessionRead(ORMModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    mode: InterviewMode
    status: InterviewSessionStatus
    expires_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    otp_verified_at: datetime | None
    interview_plan_json: dict[str, Any] | None
    graph_state_json: dict[str, Any] | None
    security_events_json: list[dict[str, Any]] | None
    created_at: datetime
    updated_at: datetime


class InterviewSessionSummaryRead(ORMModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    mode: InterviewMode
    status: InterviewSessionStatus
    expires_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    question_count: int
    evaluation_status: str


class InterviewPlanUpdate(BaseModel):
    interview_plan_json: dict[str, Any] = Field(default_factory=dict)


class InterviewInviteResponse(BaseModel):
    message: str
    expires_at: datetime


class InterviewEntryRead(BaseModel):
    session_id: UUID
    candidate_id: UUID
    job_id: UUID
    status: InterviewSessionStatus
    expires_at: datetime | None
    otp_verified: bool


class VerifyOtpRequest(BaseModel):
    otp: str = Field(min_length=4, max_length=12)


class CandidateAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)
    client_session_nonce: str | None = None


class CompleteInterviewRequest(BaseModel):
    client_session_nonce: str | None = None


class LiveInterviewTurnResponse(BaseModel):
    status: InterviewSessionStatus
    current_question_index: int
    message: str | None = None
    completed: bool = False
    client_session_nonce: str | None = None


class InterviewMessageRead(ORMModel):
    id: UUID
    interview_session_id: UUID
    role: str
    content: str
    question_type: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


class InterviewEvaluationRead(ORMModel):
    id: UUID
    interview_session_id: UUID
    candidate_id: UUID
    job_id: UUID
    overall_score: float
    competency_scores_json: list[dict[str, Any]] | dict[str, Any]
    soft_skill_scores_json: list[dict[str, Any]] | dict[str, Any]
    strengths_json: list[str]
    weaknesses_json: list[str]
    red_flags_json: list[str]
    evidence_json: list[dict[str, Any]] | dict[str, Any]
    missing_evidence_json: list[str]
    recommendation: str
    confidence: float
    created_at: datetime
    updated_at: datetime
