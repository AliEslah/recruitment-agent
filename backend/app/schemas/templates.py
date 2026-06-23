from __future__ import annotations

from pydantic import BaseModel, Field


class RoleTemplateRead(BaseModel):
    template_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    department: str = Field(min_length=1)
    seniority_examples: list[str]
    raw_jd_starter: str = Field(min_length=1)
    suggested_soft_skills: list[str]
    suggested_knockout_areas: list[str]
    suggested_fixed_interview_questions: list[str]
