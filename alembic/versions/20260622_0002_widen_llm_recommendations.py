from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260622_0002"
down_revision = "20260622_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("interview_evaluations", "recommendation", type_=sa.Text(), existing_nullable=False)
    op.alter_column("final_scorecards", "recommendation", type_=sa.Text(), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("final_scorecards", "recommendation", type_=sa.String(length=100), existing_nullable=False)
    op.alter_column("interview_evaluations", "recommendation", type_=sa.String(length=100), existing_nullable=False)
