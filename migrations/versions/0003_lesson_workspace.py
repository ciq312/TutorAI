"""Persist lesson lifecycle and editable teaching materials."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_lesson_workspace"
down_revision = "0002_context_search"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lessons", sa.Column("status", sa.String(16), nullable=False, server_default="scheduled"))
    op.add_column("lessons", sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("lessons", sa.Column("preparation_minutes", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("lessons", sa.Column("materials", postgresql.JSONB(), nullable=False, server_default="{}"))


def downgrade():
    for column in ("materials", "preparation_minutes", "duration_minutes", "status"):
        op.drop_column("lessons", column)
