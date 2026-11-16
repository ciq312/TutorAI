"""Bounded, student-scoped chat contracts. Conversations are not persisted."""
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from app.schemas.context import ContextSource
from app.schemas.data import Input
from app.schemas.knowledge import KnowledgeSource

ChatText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class ChatMessage(Input):
    role: Literal["user", "assistant"]
    content: ChatText


class ChatRequest(Input):
    message: ChatText
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


class ChatContent(Input):
    answer: str = Field(min_length=1, max_length=12000)


class ChatResponse(ChatContent):
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)
    sources: list[ContextSource]
    warnings: list[str]
