from __future__ import annotations

from typing import Any, NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class FinalDecisionState(TypedDict):
    session: AsyncSession
    candidate_id: UUID
    job_id: UUID
    candidate_score: NotRequired[dict[str, Any]]
    interview_evaluation: NotRequired[dict[str, Any]]
    final_scorecard: NotRequired[dict[str, Any]]
    errors: NotRequired[list[str]]

