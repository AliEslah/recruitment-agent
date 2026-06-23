from __future__ import annotations

from typing import Any, NotRequired, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class BaseGraphState(TypedDict):
    session: AsyncSession
    errors: NotRequired[list[str]]


class SessionState(TypedDict, total=False):
    session: AsyncSession
    errors: list[str]
    job_id: UUID
    candidate_id: UUID
    interview_session_id: UUID
    raw: dict[str, Any]

