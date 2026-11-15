"""Students, contacts and lessons."""
from alembic import op
import sqlalchemy as sa

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("grade", sa.String(100)),
        sa.Column("goals", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("relationship", sa.String(100)),
    )
    op.create_index("ix_contacts_student_id", "contacts", ["student_id"])
    op.create_table(
        "lessons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("homework", sa.Text()),
        sa.Column("difficulties", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lessons_student_scheduled", "lessons", ["student_id", "scheduled_at"])


def downgrade():
    op.drop_table("lessons")
    op.drop_table("contacts")
    op.drop_table("students")
