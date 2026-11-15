from datetime import datetime
from typing import Annotated
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
        for key in self.model_fields_set & {"name", "phone", "topic", "scheduled_at"}:
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


class LessonCreate(Input):
    scheduled_at: AwareDatetime
    topic: Topic
    notes: Note | None = None
    homework: Note | None = Field(default=None, description="Actually assigned homework")
    difficulties: Note | None = None


class LessonPatch(Patch):
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
