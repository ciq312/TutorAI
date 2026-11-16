from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Boolean, CheckConstraint, Integer, UniqueConstraint, DateTime, ForeignKey, Index, String, Text, LargeBinary, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    grade: Mapped[str | None] = mapped_column(String(100))
    goals: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(16))
    relationship: Mapped[str | None] = mapped_column(String(100))


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (Index("ix_lessons_student_scheduled", "student_id", "scheduled_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE")
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    indexing_status: Mapped[str] = mapped_column(String(16), server_default="pending")
    indexing_error: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(16), server_default="scheduled")
    duration_minutes: Mapped[int] = mapped_column(Integer, server_default="60")
    preparation_minutes: Mapped[int] = mapped_column(Integer, server_default="30")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
    homework_status: Mapped[str] = mapped_column(String(20), server_default="unknown")
    materials: Mapped[dict] = mapped_column(JSONB, server_default='{}')
    topic: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    homework: Mapped[str | None] = mapped_column(Text)
    difficulties: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("lesson_id", "position", name="uq_chunks_lesson_position"),
        CheckConstraint("vector_dims(embedding) = dimensions", name="ck_chunks_dimensions"),
        Index("ix_chunks_student_model", "student_id", "embedding_model", "dimensions"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector())
    embedding_model: Mapped[str] = mapped_column(String(200))
    dimensions: Mapped[int] = mapped_column(Integer)
    text_version: Mapped[str] = mapped_column(String(20))


class IntegrationState(Base):
    __tablename__ = "integration_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, server_default='{}')


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (UniqueConstraint("calendar_id", "external_id", name="uq_calendar_external"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    calendar_id: Mapped[str] = mapped_column(String(500))
    external_id: Mapped[str] = mapped_column(String(500))
    series_id: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(Text, server_default="")
    etag: Mapped[str] = mapped_column(String(500), server_default="")
    status: Mapped[str] = mapped_column(String(30), server_default="confirmed")
    decision: Mapped[str] = mapped_column(String(20), server_default="pending")
    lesson_id: Mapped[UUID | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), unique=True)


class CalendarSeries(Base):
    __tablename__ = "calendar_series"
    __table_args__ = (UniqueConstraint("calendar_id", "external_id", name="uq_calendar_series"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    calendar_id: Mapped[str] = mapped_column(String(500))
    external_id: Mapped[str] = mapped_column(String(500))
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))


class CalendarApproval(Base):
    __tablename__ = "calendar_approvals"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("calendar_events.id", ondelete="CASCADE"))
    homework: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    etag: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    pages: Mapped[list] = mapped_column(JSONB, server_default='[]')
    topics: Mapped[list] = mapped_column(JSONB, server_default='[]')
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    error: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    page: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector())
    model: Mapped[str] = mapped_column(String(200))
    dimensions: Mapped[int] = mapped_column(Integer)


class CurriculumAssignment(Base):
    __tablename__ = "curriculum_assignments"
    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    topic_index: Mapped[int] = mapped_column(Integer, server_default="0")


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    key: Mapped[str] = mapped_column(String(250), primary_key=True)
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    error: Mapped[str | None] = mapped_column(String(100))
    retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSONB, server_default='{}')
