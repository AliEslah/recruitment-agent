from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.common import ORMModel


class FinalScorecardRead(ORMModel):
    id: UUID
    candidate_id: UUID
    job_id: UUID
    resume_score: float
    interview_score: float
    soft_skill_score: float
    overall_fit: float
    risk_level: str
    evidence_summary_json: list[dict[str, Any]] | dict[str, Any]
    candidate_fit_narrative: str
    missing_evidence_json: list[str]
    recommendation: str
    confidence: float
    created_at: datetime
    updated_at: datetime

