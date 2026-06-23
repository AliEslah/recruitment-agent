from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[Any]: JSONB}


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    HIRING_MANAGER = "HIRING_MANAGER"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CRITERIA_GENERATED = "CRITERIA_GENERATED"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"


class CandidateStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PARSED = "PARSED"
    SCORED = "SCORED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    INTERVIEW_INVITED = "INTERVIEW_INVITED"
    INTERVIEW_ACTIVE = "INTERVIEW_ACTIVE"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    FINAL_REVIEW = "FINAL_REVIEW"
    APPROVED = "APPROVED"
    REJECTED_FINAL = "REJECTED_FINAL"


class InterviewMode(str, enum.Enum):
    CHAT = "CHAT"


class InterviewSessionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    INVITED = "INVITED"
    OTP_PENDING = "OTP_PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class InterviewMessageRole(str, enum.Enum):
    SYSTEM = "SYSTEM"
    AI = "AI"
    CANDIDATE = "CANDIDATE"


class HumanDecisionStage(str, enum.Enum):
    SHORTLIST = "SHORTLIST"
    FINAL = "FINAL"


class HumanDecisionValue(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    HOLD = "HOLD"


class SecurityEventType(str, enum.Enum):
    TOKEN_OPENED = "TOKEN_OPENED"
    OTP_SENT = "OTP_SENT"
    OTP_VERIFIED = "OTP_VERIFIED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_OTP = "INVALID_OTP"
    MULTIPLE_SESSION_ATTEMPT = "MULTIPLE_SESSION_ATTEMPT"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    seniority: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(100))
    salary_range: Mapped[str | None] = mapped_column(String(255))
    raw_jd: Mapped[str] = mapped_column(Text, nullable=False)
    improved_jd: Mapped[str | None] = mapped_column(Text)
    criteria_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    must_haves_json: Mapped[list[str] | None] = mapped_column(JSONB)
    nice_to_haves_json: Mapped[list[str] | None] = mapped_column(JSONB)
    disqualifiers_json: Mapped[list[str] | None] = mapped_column(JSONB)
    soft_skills_json: Mapped[list[str] | None] = mapped_column(JSONB)
    knockout_areas_json: Mapped[list[str] | None] = mapped_column(JSONB)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), default=JobStatus.DRAFT, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    candidates: Mapped[list[Candidate]] = relationship(back_populates="job")


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_job_id", "job_id"),
        Index("ix_candidates_status", "status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(100))
    resume_file_path: Mapped[str | None] = mapped_column(String(1024))
    resume_text: Mapped[str | None] = mapped_column(Text)
    resume_hash: Mapped[str | None] = mapped_column(String(128))
    parsed_profile_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    enriched_profile_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status"),
        default=CandidateStatus.UPLOADED,
        nullable=False,
    )

    job: Mapped[Job] = relationship(back_populates="candidates")
    scores: Mapped[list[CandidateScore]] = relationship(back_populates="candidate")
    interview_sessions: Mapped[list[InterviewSession]] = relationship(back_populates="candidate")
    final_scorecards: Mapped[list[FinalScorecard]] = relationship(back_populates="candidate")
    human_decisions: Mapped[list[HumanDecision]] = relationship(back_populates="candidate")


class CandidateScore(TimestampMixin, Base):
    __tablename__ = "candidate_scores"
    __table_args__ = (Index("ix_candidate_scores_candidate_job_created", "candidate_id", "job_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    criteria_scores_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    strengths_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    weaknesses_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    risks_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    evidence_json: Mapped[list[dict[str, Any]] | dict[str, Any] | None] = mapped_column(JSONB)
    recommendation: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="scores")


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (Index("ix_interview_sessions_candidate_job_status", "candidate_id", "job_id", "status"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    mode: Mapped[InterviewMode] = mapped_column(Enum(InterviewMode, name="interview_mode"), default=InterviewMode.CHAT, nullable=False)
    status: Mapped[InterviewSessionStatus] = mapped_column(
        Enum(InterviewSessionStatus, name="interview_session_status"),
        default=InterviewSessionStatus.DRAFT,
        nullable=False,
    )
    secure_token_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    otp_hash: Mapped[str | None] = mapped_column(String(255))
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    otp_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    single_session_lock: Mapped[str | None] = mapped_column(String(128))
    client_session_hash: Mapped[str | None] = mapped_column(String(128))
    interview_plan_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    graph_state_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    security_events_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)

    candidate: Mapped[Candidate] = relationship(back_populates="interview_sessions")
    messages: Mapped[list[InterviewMessage]] = relationship(back_populates="interview_session")
    evaluations: Mapped[list[InterviewEvaluation]] = relationship(back_populates="interview_session")


class InterviewMessage(Base):
    __tablename__ = "interview_messages"
    __table_args__ = (Index("ix_interview_messages_session_created", "interview_session_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    interview_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    role: Mapped[InterviewMessageRole] = mapped_column(Enum(InterviewMessageRole, name="interview_message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    interview_session: Mapped[InterviewSession] = relationship(back_populates="messages")


class InterviewEvaluation(TimestampMixin, Base):
    __tablename__ = "interview_evaluations"
    __table_args__ = (Index("ix_interview_evaluations_session_created", "interview_session_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    interview_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    competency_scores_json: Mapped[list[dict[str, Any]] | dict[str, Any]] = mapped_column(JSONB, nullable=False)
    soft_skill_scores_json: Mapped[list[dict[str, Any]] | dict[str, Any]] = mapped_column(JSONB, nullable=False)
    strengths_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    weaknesses_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    red_flags_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    evidence_json: Mapped[list[dict[str, Any]] | dict[str, Any]] = mapped_column(JSONB, nullable=False)
    missing_evidence_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    interview_session: Mapped[InterviewSession] = relationship(back_populates="evaluations")


class FinalScorecard(TimestampMixin, Base):
    __tablename__ = "final_scorecards"
    __table_args__ = (Index("ix_final_scorecards_candidate_job_created", "candidate_id", "job_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    resume_score: Mapped[float] = mapped_column(Float, nullable=False)
    interview_score: Mapped[float] = mapped_column(Float, nullable=False)
    soft_skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_fit: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_summary_json: Mapped[list[dict[str, Any]] | dict[str, Any]] = mapped_column(JSONB, nullable=False)
    candidate_fit_narrative: Mapped[str] = mapped_column(Text, nullable=False)
    missing_evidence_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="final_scorecards")


class HumanDecision(Base):
    __tablename__ = "human_decisions"
    __table_args__ = (Index("ix_human_decisions_candidate_job_stage_created", "candidate_id", "job_id", "stage", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    stage: Mapped[HumanDecisionStage] = mapped_column(Enum(HumanDecisionStage, name="human_decision_stage"), nullable=False)
    decision: Mapped[HumanDecisionValue] = mapped_column(Enum(HumanDecisionValue, name="human_decision_value"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="human_decisions")


class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    __table_args__ = (Index("ix_communication_logs_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jobs.id"))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("candidates.id"))
    interview_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("interview_sessions.id"))
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LlmCallLog(Base):
    __tablename__ = "llm_call_logs"
    __table_args__ = (
        Index("ix_llm_call_logs_task_status_created", "task", "status", "created_at"),
        Index("ix_llm_call_logs_input_hash", "input_hash"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    task: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    raw_response_path: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LlmCache(TimestampMixin, Base):
    __tablename__ = "llm_cache"

    id: Mapped[uuid.UUID] = uuid_pk()
    task: Mapped[str] = mapped_column(String(255), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    output_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class QuestionBankItem(TimestampMixin, Base):
    __tablename__ = "question_bank_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_family: Mapped[str | None] = mapped_column(String(255))
    seniority: Mapped[str | None] = mapped_column(String(100))
    question_type: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
