from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.data import Input, Name, Topic, Note


class CurriculumTopic(Input):
    title: Topic
    objectives: Note = ''
    page: int = Field(default=1, ge=1, le=500)


class CurriculumTopics(Input):
    topics: list[CurriculumTopic] = Field(min_length=1, max_length=200)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    filename: str
    kind: str
    status: str
    error: str | None
    topics: list[CurriculumTopic]
    created_at: datetime


class KnowledgeSearch(Input):
    query: Topic
    limit: int = Field(default=5, ge=1, le=10)


class KnowledgeSource(BaseModel):
    document_id: UUID
    title: str
    page: int
    text: str
    distance: float


class AssignmentInput(Input):
    document_id: UUID
    topic_index: int = Field(default=0, ge=0, le=199)
