from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.db.models import CandidateStatus
from app.schemas.common import ORMModel


class CandidateCreate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class CandidateRead(ORMModel):
    id: UUID
    job_id: UUID
    name: str | None
    email: str | None
    phone: str | None
    resume_file_path: str | None
    resume_text: str | None
    resume_hash: str | None
    parsed_profile_json: dict[str, Any] | None
    enriched_profile_json: dict[str, Any] | None
    status: CandidateStatus
    created_at: datetime
    updated_at: datetime


class CandidateScoreSummaryRead(ORMModel):
    id: UUID
    overall_score: float
    recommendation: str
    confidence: float
    created_at: datetime


class CandidateListRead(CandidateRead):
    latest_score: CandidateScoreSummaryRead | None = None


class CandidateScoreRead(ORMModel):
    id: UUID
    candidate_id: UUID
    job_id: UUID
    overall_score: float
    criteria_scores_json: list[dict[str, Any]]
    strengths_json: list[str]
    weaknesses_json: list[str]
    risks_json: list[str]
    evidence_json: list[dict[str, Any]] | dict[str, Any] | None
    recommendation: str
    confidence: float
    created_at: datetime
    updated_at: datetime


class CandidateProcessRequest(BaseModel):
    force: bool = False
