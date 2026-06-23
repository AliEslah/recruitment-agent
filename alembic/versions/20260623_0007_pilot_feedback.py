from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260623_0007"
down_revision = "20260623_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "pilot_feedback" not in inspector.get_table_names():
        op.create_table(
            "pilot_feedback",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("interview_session_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("feedback_type", sa.String(length=100), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
            sa.ForeignKeyConstraint(["interview_session_id"], ["interview_sessions.id"]),
            sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {index["name"] for index in inspector.get_indexes("pilot_feedback")}
    if "ix_pilot_feedback_created_at" not in existing_indexes:
        op.create_index("ix_pilot_feedback_created_at", "pilot_feedback", ["created_at"])
    if "ix_pilot_feedback_type_created" not in existing_indexes:
        op.create_index("ix_pilot_feedback_type_created", "pilot_feedback", ["feedback_type", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "pilot_feedback" in inspector.get_table_names():
        op.drop_index("ix_pilot_feedback_type_created", table_name="pilot_feedback")
        op.drop_index("ix_pilot_feedback_created_at", table_name="pilot_feedback")
        op.drop_table("pilot_feedback")
