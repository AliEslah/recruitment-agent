from __future__ import annotations

from alembic import op


revision = "20260622_0004"
down_revision = "20260622_0003"
branch_labels = None
depends_on = None


INDEXES = [
    ("ix_candidates_job_id", "candidates", "job_id"),
    ("ix_candidates_status", "candidates", "status"),
    ("ix_candidate_scores_candidate_job_created", "candidate_scores", "candidate_id, job_id, created_at"),
    ("ix_interview_sessions_candidate_job_status", "interview_sessions", "candidate_id, job_id, status"),
    ("ix_interview_messages_session_created", "interview_messages", "interview_session_id, created_at"),
    ("ix_interview_evaluations_session_created", "interview_evaluations", "interview_session_id, created_at"),
    ("ix_final_scorecards_candidate_job_created", "final_scorecards", "candidate_id, job_id, created_at"),
    ("ix_human_decisions_candidate_job_stage_created", "human_decisions", "candidate_id, job_id, stage, created_at"),
    ("ix_audit_logs_entity_created", "audit_logs", "entity_type, entity_id, created_at"),
    ("ix_audit_logs_created_at", "audit_logs", "created_at"),
    ("ix_communication_logs_created_at", "communication_logs", "created_at"),
    ("ix_llm_call_logs_task_status_created", "llm_call_logs", "task, status, created_at"),
    ("ix_llm_call_logs_input_hash", "llm_call_logs", "input_hash"),
]


def upgrade() -> None:
    op.execute("ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS client_session_hash VARCHAR(128)")
    for name, table, columns in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})")


def downgrade() -> None:
    for name, _, _ in reversed(INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
    op.execute("ALTER TABLE interview_sessions DROP COLUMN IF EXISTS client_session_hash")
