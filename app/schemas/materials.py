"""Separate contracts for editable teaching materials."""
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.data import Input, Topic, Note
from app.schemas.context import ContextSource
from app.schemas.knowledge import KnowledgeSource


class PlanRequest(Input):
    instructions: Topic | None = None
    topic: Topic
    duration_minutes: int = Field(default=60, ge=10, le=240)


class HomeworkRequest(Input):
    instructions: Topic = "Закрепить материал занятия"
    duration_minutes: int = Field(default=20, ge=5, le=180)
    include_answers: bool = False


class FeedbackRequest(Input):
    recipient: Literal["student", "parent"] = "student"
    instructions: Topic = "Коротко и понятно описать результаты занятия и следующий шаг"


class Fact(Input):
    text: str = Field(min_length=1, max_length=3000)
    source_numbers: list[int] = Field(min_length=1, max_length=20)


class GeneratedMaterial(Input):
    facts: list[Fact] = Field(max_length=30)
    missing_data: list[str] = Field(max_length=20)


class PlanContent(GeneratedMaterial):
    brief: str = Field(min_length=1, max_length=10000)
    plan: str = Field(min_length=1, max_length=16000)


class HomeworkContent(GeneratedMaterial):
    homework: str = Field(min_length=1, max_length=20000)
    teacher_answers: str = Field(max_length=20000)


class FeedbackContent(GeneratedMaterial):
    feedback: str = Field(min_length=1, max_length=10000)


class PlanResponse(PlanContent):
    student_id: UUID
    sources: list[ContextSource]
    warnings: list[str]
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)


class HomeworkResponse(HomeworkContent):
    student_id: UUID
    sources: list[ContextSource]
    warnings: list[str]
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)


class FeedbackResponse(FeedbackContent):
    student_id: UUID
    sources: list[ContextSource]
    warnings: list[str]
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)


class ResultsContent(GeneratedMaterial):
    summary: str = Field(min_length=1, max_length=10000)
    homework: str = Field(min_length=1, max_length=20000)
    teacher_answers: str = Field(max_length=20000)
    next_topic: str = Field(min_length=1, max_length=500)
    next_plan: str = Field(min_length=1, max_length=16000)
    brief: str = Field(min_length=1, max_length=10000)


class ResultsRequest(Input):
    instructions: Topic = "Подготовь итоги, ДЗ и следующий урок по КТП и результатам занятия"
    duration_minutes: int = Field(default=60, ge=10, le=240)


class ResultsReview(Input):
    version: UUID
    summary: Note = Field(min_length=1)
    homework: Note = Field(min_length=1)
    teacher_answers: Note = ""
    next_topic: Topic
    next_plan: Note = Field(min_length=1)
    brief: Note = Field(min_length=1)


class AcceptHomework(Input):
    homework: Note = Field(min_length=1)
