from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import Text

from app.db.models import (
    AuditLog,
    Candidate,
    CandidateScore,
    CommunicationLog,
    FinalScorecard,
    HumanDecision,
    InterviewEvaluation,
    InterviewMessage,
    InterviewSession,
    LlmCallLog,
    Job,
)
from app.schemas.llm_outputs import FinalScorecardOutput, InterviewEvaluationOutput

ROOT = Path(__file__).resolve().parents[2]


def index_names(model) -> set[str]:
    return {index.name for index in model.__table__.indexes}


def test_expected_model_indexes_are_declared() -> None:
    assert "ix_candidates_job_id" in index_names(Candidate)
    assert "ix_candidates_status" in index_names(Candidate)
    assert "ix_candidate_scores_candidate_job_created" in index_names(CandidateScore)
    assert "ix_interview_sessions_candidate_job_status" in index_names(InterviewSession)
    assert "ix_interview_messages_session_created" in index_names(InterviewMessage)
    assert "ix_interview_evaluations_session_created" in index_names(InterviewEvaluation)
    assert "ix_final_scorecards_candidate_job_created" in index_names(FinalScorecard)
    assert "ix_human_decisions_candidate_job_stage_created" in index_names(HumanDecision)
    assert "ix_audit_logs_entity_created" in index_names(AuditLog)
    assert "ix_audit_logs_created_at" in index_names(AuditLog)
    assert "ix_communication_logs_created_at" in index_names(CommunicationLog)
    assert "ix_llm_call_logs_task_status_created" in index_names(LlmCallLog)
    assert "ix_llm_call_logs_input_hash" in index_names(LlmCallLog)


def test_index_migration_is_present() -> None:
    migration = ROOT / "alembic/versions/20260622_0004_reliability_indexes_nonce.py"
    text = migration.read_text()

    for expected in [
        "client_session_hash",
        "ix_candidates_job_id",
        "ix_interview_messages_session_created",
        "ix_llm_call_logs_task_status_created",
    ]:
        assert expected in text


def test_unused_scaffold_is_removed_and_not_packaged() -> None:
    assert not (ROOT / "src/recruitment_agent").exists()
    assert not (ROOT / "archive").exists()
    assert "COPY src" not in (ROOT / "Dockerfile").read_text()
    assert 'packages = ["backend/app"]' in (ROOT / "pyproject.toml").read_text()


def test_interview_mode_is_chat_only() -> None:
    from app.db.models import InterviewMode

    assert [mode.value for mode in InterviewMode] == ["CHAT"]


def test_chat_only_interview_mode_migration_is_present() -> None:
    migration = ROOT / "alembic/versions/20260622_0005_chat_only_interview_mode.py"
    text = migration.read_text()

    assert "CREATE TYPE interview_mode AS ENUM ('CHAT')" in text
    assert "VOICE" in text
    assert "VIDEO" in text


def test_relationships_are_conservative() -> None:
    assert "delete-orphan" not in Job.candidates.property.cascade
    assert Candidate.scores.property.back_populates == "candidate"
    assert InterviewSession.messages.property.back_populates == "interview_session"
    assert InterviewSession.evaluations.property.back_populates == "interview_session"


def test_runtime_resume_uploads_are_ignored_and_fixture_exists() -> None:
    assert (ROOT / "tests/fixtures/resumes/jane_backend.txt").is_file()
    gitignore = (ROOT / ".gitignore").read_text()
    assert "backend/data/resumes/" in gitignore


def test_pytest_markers_are_registered() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    for marker in ["unit:", "db:", "mailpit:", "lmstudio:", "e2e:"]:
        assert marker in pyproject


def test_recommendation_schema_and_db_columns_are_aligned() -> None:
    assert isinstance(InterviewEvaluation.__table__.c.recommendation.type, Text)
    assert isinstance(FinalScorecard.__table__.c.recommendation.type, Text)

    long_recommendation = "x" * 2001
    with pytest.raises(ValidationError):
        InterviewEvaluationOutput(
            overall_score=80,
            competency_scores=[],
            soft_skill_scores=[],
            evidence=[],
            recommendation=long_recommendation,
            confidence=75,
        )
    with pytest.raises(ValidationError):
        FinalScorecardOutput(
            overall_fit=80,
            resume_score=80,
            interview_score=80,
            soft_skill_score=80,
            risk_level="LOW",
            evidence_summary=[],
            candidate_fit_narrative="Fit.",
            recommendation=long_recommendation,
            confidence=75,
        )
