from __future__ import annotations

from alembic import op


revision = "20260622_0005"
down_revision = "20260622_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE interview_sessions SET mode = 'CHAT' WHERE mode::text IN ('VOICE', 'VIDEO')")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode DROP DEFAULT")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode TYPE VARCHAR(16) USING mode::text")
    op.execute("DROP TYPE interview_mode")
    op.execute("CREATE TYPE interview_mode AS ENUM ('CHAT')")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode TYPE interview_mode USING mode::text::interview_mode")


def downgrade() -> None:
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode DROP DEFAULT")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode TYPE VARCHAR(16) USING mode::text")
    op.execute("DROP TYPE interview_mode")
    op.execute("CREATE TYPE interview_mode AS ENUM ('CHAT', 'VOICE', 'VIDEO')")
    op.execute("ALTER TABLE interview_sessions ALTER COLUMN mode TYPE interview_mode USING mode::text::interview_mode")
