from __future__ import annotations

from typing import Any, NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class JobCalibrationState(TypedDict):
    session: AsyncSession
    job_id: UUID
    raw_jd: NotRequired[str]
    title: NotRequired[str]
    department: NotRequired[str | None]
    seniority: NotRequired[str | None]
    location: NotRequired[str | None]
    employment_type: NotRequired[str | None]
    improved_jd: NotRequired[str]
    missing_info: NotRequired[list[str]]
    criteria: NotRequired[list[dict[str, Any]]]
    must_haves: NotRequired[list[str]]
    nice_to_haves: NotRequired[list[str]]
    disqualifiers: NotRequired[list[str]]
    soft_skills: NotRequired[list[str]]
    knockout_areas: NotRequired[list[str]]
    errors: NotRequired[list[str]]

