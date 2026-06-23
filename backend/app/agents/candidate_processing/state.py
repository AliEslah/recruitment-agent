from __future__ import annotations

from typing import Any, NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class CandidateProcessingState(TypedDict):
    session: AsyncSession
    candidate_id: UUID
    job_id: UUID
    force: NotRequired[bool]
    resume_text: NotRequired[str]
    resume_hash: NotRequired[str | None]
    parsed_profile: NotRequired[dict[str, Any]]
    extracted_links: NotRequired[list[str]]
    enriched_profile: NotRequired[dict[str, Any]]
    job_criteria: NotRequired[list[dict[str, Any]]]
    candidate_score: NotRequired[dict[str, Any]]
    skip_processing: NotRequired[bool]
    must_haves: NotRequired[list[str]]
    disqualifiers: NotRequired[list[str]]
    errors: NotRequired[list[str]]
