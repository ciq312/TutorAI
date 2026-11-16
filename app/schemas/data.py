from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Grade = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Topic = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20000)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+[1-9][0-9]{7,14}$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Patch(Input):
    @model_validator(mode="after")
    def reject_null_required_fields(self):
        # Omitted fields stay unchanged; null only clears optional fields.
        for key in self.model_fields_set & {"name", "phone", "topic", "scheduled_at", "status", "duration_minutes", "preparation_minutes", "materials", "notifications_enabled", "homework_status"}:
            if getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class StudentCreate(Input):
    name: Name
    grade: Grade | None = None
    goals: Note | None = None


class StudentPatch(Patch):
    name: Name | None = None
    grade: Grade | None = None
    goals: Note | None = None


class StudentRead(StudentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


class ContactCreate(Input):
    name: Name
    phone: Phone = Field(description="International format, e.g. +375291234567")
    relationship: Grade | None = None


class ContactPatch(Patch):
    name: Name | None = None
    phone: Phone | None = None
    relationship: Grade | None = None


class ContactRead(ContactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID


class StoredSource(Input):
    lesson_id: Annotated[str, StringConstraints(max_length=100)]
    scheduled_at: Annotated[str, StringConstraints(max_length=100)]
    excerpts: list[Note] = Field(default_factory=list, max_length=20)


class LessonDraft(Input):
    knowledge_sources: list[dict] = Field(default_factory=list, max_length=10)
    missing_data: list[Note] = Field(default_factory=list, max_length=20)
    warnings: list[Grade] = Field(default_factory=list, max_length=20)
    text: Note = ""
    brief: Note = ""
    answers: Note = ""
    sources: list[StoredSource] = Field(default_factory=list, max_length=20)


class LessonMaterials(Input):
    plan: LessonDraft | None = None
    homework: LessonDraft | None = None
    feedback: LessonDraft | None = None
    next_plan: LessonDraft | None = None
    next_topic: Topic | None = None
    results: dict | None = None


class LessonCreate(Input):
    notifications_enabled: bool = True
    homework_status: Literal["unknown", "done", "partial", "not_done"] = "unknown"
    status: Literal["scheduled", "completed", "cancelled"] = "scheduled"
    duration_minutes: int = Field(default=60, ge=10, le=240)
    preparation_minutes: int = Field(default=30, ge=0, le=10080)
    materials: LessonMaterials = Field(default_factory=LessonMaterials)
    scheduled_at: AwareDatetime
    topic: Topic
    notes: Note | None = None
    homework: Note | None = Field(default=None, description="Actually assigned homework")
    difficulties: Note | None = None


class LessonPatch(Patch):
    notifications_enabled: bool | None = None
    homework_status: Literal["unknown", "done", "partial", "not_done"] | None = None
    status: Literal["scheduled", "completed", "cancelled"] | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=240)
    preparation_minutes: int | None = Field(default=None, ge=0, le=10080)
    materials: LessonMaterials | None = None
    scheduled_at: AwareDatetime | None = None
    topic: Topic | None = None
    notes: Note | None = None
    homework: Note | None = None
    difficulties: Note | None = None


class LessonRead(LessonCreate):
    indexing_status: str
    indexing_error: str | None
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    created_at: datetime
