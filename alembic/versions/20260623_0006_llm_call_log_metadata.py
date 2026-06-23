from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260623_0006"
down_revision = "20260622_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("llm_call_logs")}
    if "metadata_json" not in columns:
        op.add_column(
            "llm_call_logs",
            sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("llm_call_logs")}
    if "metadata_json" in columns:
        op.drop_column("llm_call_logs", "metadata_json")
