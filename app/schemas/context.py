from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from app.schemas.data import Input


class ContextRequest(Input):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    recent_lessons_limit: int = Field(default=3, ge=0, le=10)
    semantic_limit: int = Field(default=5, ge=0, le=20)
    max_distance: float = Field(default=0.7, ge=0, le=2)
    max_context_chars: int = Field(default=12000, ge=500, le=30000)
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        return self


class ContextSource(BaseModel):
    lesson_id: UUID
    scheduled_at: datetime
    reasons: list[Literal["recent", "semantic"]]
    excerpts: list[str]
    distance: float | None


class ContextResponse(BaseModel):
    student_id: UUID
    sources: list[ContextSource]
    semantic_status: Literal["ready", "empty", "unavailable", "disabled"]
    unindexed_lessons: int
    warnings: list[str]
