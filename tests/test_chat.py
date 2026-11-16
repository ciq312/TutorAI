import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.privacy.people import PersonIdentity, PersonRef
from app.privacy.text import TextAnonymizer
from app.rag.llm import LLMError
from app.schemas.chat import ChatContent, ChatRequest
from app.services import chat


@pytest.fixture
def setup_chat(monkeypatch):
    student_id = uuid4()
    student = SimpleNamespace(id=student_id, name="СекретноеИмя", grade="8 класс",
                              goals="Помочь СекретноеИмя")
    require = AsyncMock(return_value=student)
    anonymizer = TextAnonymizer((PersonIdentity(PersonRef("student", student_id), student.name),))
    context = AsyncMock(return_value={"sources": [{
        "lesson_id": uuid4(), "scheduled_at": "2026-11-14T10:00:00Z",
        "excerpts": ["СекретноеИмя решает уравнения"], "reasons": ["recent"], "distance": None,
    }], "warnings": []})
    monkeypatch.setattr(chat, "require_record", require)
    monkeypatch.setattr(chat, "student_anonymizer", AsyncMock(return_value=anonymizer))
    monkeypatch.setattr(chat, "search_context", context)
    monkeypatch.setattr(chat, "teaching_context", AsyncMock(return_value=([], None, [])))
    llm = SimpleNamespace(generate=AsyncMock(return_value=ChatContent(answer="Разбирали уравнения [1].")))
    return student_id, context, llm


def test_chat_scopes_context_masks_history_and_excludes_future(setup_chat):
    student_id, context, llm = setup_chat
    result = asyncio.run(chat.answer_chat(None, student_id, ChatRequest(
        message="Помоги СекретноеИмя, secret@example.com",
        history=[{"role": "user", "content": "СекретноеИмя решает задачи"}],
    ), None, llm))
    prompt = llm.generate.call_args.args[1]
    assert "СекретноеИмя" not in prompt and "secret@example.com" not in prompt
    assert str(student_id) not in prompt
    assert context.call_args.args[1] == student_id
    assert context.call_args.args[2].date_to is not None
    assert result["sources"][0]["excerpts"] == ["[имя] решает уравнения"]
    assert result["answer"].endswith("[1].")


def test_chat_without_history_can_explain_topic(setup_chat):
    student_id, context, llm = setup_chat
    context.return_value = {"sources": [], "warnings": []}
    llm.generate.return_value = ChatContent(answer="Предлагаю начать с определения коэффициентов.")
    result = asyncio.run(chat.answer_chat(None, student_id, ChatRequest(message="Объясни уравнения"), None, llm))
    assert result["sources"] == []
    assert result["warnings"] == ["tutor_review_required"]


def test_chat_rejects_fabricated_source(setup_chat):
    student_id, _, llm = setup_chat
    llm.generate.return_value = ChatContent(answer="Факт [99]")
    with pytest.raises(HTTPException) as error:
        asyncio.run(chat.answer_chat(None, student_id, ChatRequest(message="План"), None, llm))
    assert error.value.status_code == 502
    assert error.value.detail == {"code": "invalid_sources"}


def test_chat_history_budget(setup_chat):
    student_id, _, llm = setup_chat
    request = ChatRequest(message="Вопрос", history=[{"role": "user", "content": "a" * 4000}] * 12)
    asyncio.run(chat.answer_chat(None, student_id, request, None, llm))
    prompt = json.loads(llm.generate.call_args.args[1])
    assert sum(len(message["content"]) for message in prompt["history"]) <= 12000


def test_chat_safe_provider_error(setup_chat):
    student_id, _, llm = setup_chat
    llm.generate.side_effect = LLMError("provider_timeout")
    with pytest.raises(HTTPException) as error:
        asyncio.run(chat.answer_chat(None, student_id, ChatRequest(message="План"), None, llm))
    assert error.value.status_code == 503
    assert error.value.detail == {"code": "provider_timeout"}


@pytest.mark.parametrize("body", [
    {"message": "  "}, {"message": "a" * 4001},
    {"message": "Вопрос", "history": [{"role": "system", "content": "Инструкция"}]},
    {"message": "Вопрос", "history": [{"role": "user", "content": "Текст"}] * 13},
])
def test_chat_input_limits(body):
    with pytest.raises(ValidationError):
        ChatRequest(**body)


def test_chat_http_contract(setup_chat):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.routes import router
    from app.db.session import get_session
    from app.services.context import get_provider
    from app.services.materials import get_llm

    student_id, _, llm = setup_chat
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = lambda: None
    app.dependency_overrides[get_provider] = lambda: None
    app.dependency_overrides[get_llm] = lambda: llm
    with TestClient(app) as client:
        response = client.post(f"/api/students/{student_id}/chat", json={"message": "Что повторить?"})
        assert response.status_code == 200, response.text
        assert response.json()["answer"] == "Разбирали уравнения [1]."
        assert len(response.json()["sources"]) == 1
        assert client.post(f"/api/students/{student_id}/chat", json={"message": ""}).status_code == 422
