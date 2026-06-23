from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import JobStatus
from app.schemas.common import ORMModel


class JobCreate(BaseModel):
    title: str = Field(min_length=1)
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    employment_type: str | None = None
    salary_range: str | None = None
    raw_jd: str = Field(min_length=1)
    created_by_id: UUID | None = None


class JobCriteriaUpdate(BaseModel):
    improved_jd: str | None = None
    criteria_json: list[dict[str, Any]] | None = None
    must_haves_json: list[str] | None = None
    nice_to_haves_json: list[str] | None = None
    disqualifiers_json: list[str] | None = None
    soft_skills_json: list[str] | None = None
    knockout_areas_json: list[str] | None = None


class JobRead(ORMModel):
    id: UUID
    title: str
    department: str | None
    seniority: str | None
    location: str | None
    employment_type: str | None
    salary_range: str | None
    raw_jd: str
    improved_jd: str | None
    criteria_json: list[dict[str, Any]] | None
    must_haves_json: list[str] | None
    nice_to_haves_json: list[str] | None
    disqualifiers_json: list[str] | None
    soft_skills_json: list[str] | None
    knockout_areas_json: list[str] | None
    status: JobStatus
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime

