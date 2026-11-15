"""Lesson indexing state and pgvector chunks."""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0002_context_search"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("lessons", sa.Column("indexing_status", sa.String(16), server_default="pending", nullable=False))
    op.add_column("lessons", sa.Column("indexing_error", sa.String(100)))
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("embedding_model", sa.String(200), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("text_version", sa.String(20), nullable=False),
        sa.UniqueConstraint("lesson_id", "position", name="uq_chunks_lesson_position"),
        sa.CheckConstraint("vector_dims(embedding) = dimensions", name="ck_chunks_dimensions"),
    )
    op.create_index("ix_chunks_student_model", "document_chunks", ["student_id", "embedding_model", "dimensions"])


def downgrade():
    op.drop_table("document_chunks")
    op.drop_column("lessons", "indexing_error")
    op.drop_column("lessons", "indexing_status")
    # The extension can be shared by other applications; leave it installed.
