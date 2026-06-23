from __future__ import annotations

from typing import Any, NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class InterviewPlanningState(TypedDict):
    session: AsyncSession
    candidate_id: UUID
    job_id: UUID
    job_criteria: NotRequired[list[dict[str, Any]]]
    candidate_profile: NotRequired[dict[str, Any]]
    candidate_score: NotRequired[dict[str, Any]]
    interview_plan: NotRequired[dict[str, Any]]
    interview_session_id: NotRequired[UUID]
    errors: NotRequired[list[str]]


class LiveInterviewState(TypedDict):
    session: AsyncSession
    interview_session_id: UUID
    candidate_id: NotRequired[UUID]
    job_id: NotRequired[UUID]
    status: NotRequired[str]
    current_question_index: NotRequired[int]
    questions: NotRequired[list[dict[str, Any]]]
    transcript: NotRequired[list[dict[str, Any]]]
    last_candidate_answer: NotRequired[str | None]
    follow_up_count: NotRequired[int]
    max_follow_ups: NotRequired[int]
    next_message: NotRequired[str | None]
    completed: NotRequired[bool]
    needs_follow_up: NotRequired[bool]
    errors: NotRequired[list[str]]


class InterviewEvaluationState(TypedDict):
    session: AsyncSession
    interview_session_id: UUID
    candidate_id: NotRequired[UUID]
    job_id: NotRequired[UUID]
    transcript: NotRequired[list[dict[str, Any]]]
    job_criteria: NotRequired[list[dict[str, Any]]]
    candidate_profile: NotRequired[dict[str, Any]]
    resume_score: NotRequired[dict[str, Any]]
    interview_evaluation: NotRequired[dict[str, Any]]
    errors: NotRequired[list[str]]

