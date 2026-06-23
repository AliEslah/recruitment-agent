from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    service: str


class IdResponse(BaseModel):
    id: UUID


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class AuditLogRead(ORMModel):
    id: UUID
    actor_user_id: UUID | None
    entity_type: str
    entity_id: UUID
    action: str
    metadata_json: dict[str, Any] | None
    created_at: datetime


class LlmCallLogRead(ORMModel):
    id: UUID
    task: str
    model: str
    input_hash: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    cache_hit: bool
    status: str
    error: str | None
    raw_response_path: str | None
    created_at: datetime


class CommunicationLogRead(ORMModel):
    id: UUID
    job_id: UUID | None
    candidate_id: UUID | None
    interview_session_id: UUID | None
    provider: str
    channel: str
    recipient: str
    subject: str
    body: str
    status: str
    metadata_json: dict[str, Any] | None
    created_at: datetime


class HumanDecisionCreate(BaseModel):
    decision: str = Field(pattern="^(APPROVE|REJECT|HOLD)$")
    reason: str = Field(min_length=1)
    comment: str | None = None
