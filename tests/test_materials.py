import asyncio
import json

import httpx
import pytest

from app.core.config import Settings
from app.rag.llm import HTTPModel, LLMError
from app.schemas.materials import PlanContent
from app.services.materials import get_llm


class FakeLLM:
    def __init__(self, invalid=False):
        self.prompts = []
        self.invalid = invalid

    async def generate(self, system, prompt, schema):
        self.prompts.append(prompt)
        common = {"facts": [{"text": "Изучали уравнения", "source_numbers": [99 if self.invalid else 1]}], "missing_data": ["Выполнение ДЗ неизвестно"]}
        fields = {"PlanContent": {"brief": "Уравнения [1]", "plan": "Предложение: практика 60 минут"},
                  "HomeworkContent": {"homework": "Решите x + 2 = 5", "teacher_answers": "x = 3"},
                  "FeedbackContent": {"feedback": "Изучали уравнения [1]. Предлагаю закрепить материал."}}
        return schema(**common, **fields[schema.__name__])


def records(client):
    student = client.post("/api/students", json={"name": "СекретноеИмя", "goals": "Помочь СекретноеИмя"}).json()
    lesson = client.post(f"/api/students/{student['id']}/lessons", json={
        "topic": "Уравнения", "scheduled_at": "2026-11-14T10:00:00Z",
        "notes": "СекретноеИмя изучает уравнения, email: secret@example.com"}).json()
    return student, lesson


def test_three_scenarios_and_acceptance(client):
    fake = FakeLLM()
    client.app.dependency_overrides[get_llm] = lambda: fake
    student, lesson = records(client)
    other = client.post("/api/students", json={"name": "Другой"}).json()
    client.post(f"/api/students/{other['id']}/lessons", json={"topic": "ЧужойКонтекст", "scheduled_at": "2026-11-14T10:00:00Z"})
    for url, body in [
        (f"/api/students/{student['id']}/lesson-plan", {"topic": "Уравнения"}),
        (f"/api/lessons/{lesson['id']}/homework/draft", {}),
        (f"/api/lessons/{lesson['id']}/feedback/draft", {"recipient": "parent"}),
    ]:
        response = client.post(url, json=body)
        assert response.status_code == 200, response.text
        assert response.json()["sources"][0]["lesson_id"] == lesson["id"]
        if "teacher_answers" in response.json():
            assert response.json()["teacher_answers"] == ""
    assert all("СекретноеИмя" not in p and "secret@example.com" not in p and "ЧужойКонтекст" not in p for p in fake.prompts)
    assert client.get(f"/api/lessons/{lesson['id']}").json()["homework"] is None
    accepted = client.put(f"/api/lessons/{lesson['id']}/homework", json={"homework": "Проверенное ДЗ"})
    assert accepted.status_code == 200
    assert accepted.json()["homework"] == "Проверенное ДЗ"
    assert accepted.json()["indexing_status"] == "failed"  # saved despite missing embedding key
    assert client.get(f"/api/lessons/{lesson['id']}").json()["homework"] == "Проверенное ДЗ"


def test_empty_history_and_invalid_sources(client):
    fake = FakeLLM(invalid=True)
    client.app.dependency_overrides[get_llm] = lambda: fake
    student = client.post("/api/students", json={"name": "Новый"}).json()
    url = f"/api/students/{student['id']}/lesson-plan"
    empty = client.post(url, json={"topic": "Уравнения"})
    assert empty.status_code == 200
    assert empty.json()["facts"] == []
    assert empty.json()["missing_data"]
    assert fake.prompts == []
    student, lesson = records(client)
    bad = client.post(f"/api/lessons/{lesson['id']}/feedback/draft", json={})
    assert bad.status_code == 502
    assert bad.json()["detail"]["code"] == "invalid_sources"


@pytest.mark.parametrize("provider", ["gemini", "ollama"])
def test_llm_http_contract(provider):
    async def run():
        def handle(request):
            body = json.loads(request.content)
            result = {"facts": [], "missing_data": [], "brief": "Бриф", "plan": "План"}
            if provider == "gemini":
                assert body["generationConfig"]["responseJsonSchema"]
                return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(result)}]}}]})
            assert body["stream"] is False
            assert body["format"]
            return httpx.Response(200, json={"done": True, "message": {"content": json.dumps(result)}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            model = HTTPModel(Settings(database_url="postgresql://a:b@localhost/test", llm_provider=provider, gemini_api_key="test"), client)
            assert (await model.generate("system", "prompt", PlanContent)).plan == "План"
    asyncio.run(run())


@pytest.mark.parametrize("status,code", [(429, "rate_limited"), (403, "provider_access_denied"), (500, "provider_error"), (200, "invalid_response")])
def test_safe_llm_errors(status, code):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(status, text="private provider body"))) as client:
            model = HTTPModel(Settings(database_url="postgresql://a:b@localhost/test", gemini_api_key="test"), client)
            with pytest.raises(LLMError, match=f"^{code}$"):
                await model.generate("system", "private text", PlanContent)
    asyncio.run(run())


def test_missing_key_and_input_validation(client):
    student, lesson = records(client)
    # Explicit override keeps this test independent of local LLM settings.
    async def missing_key():
        class Missing:
            async def generate(self, *args):
                raise LLMError("missing_api_key")
        return Missing()
    client.app.dependency_overrides[get_llm] = missing_key
    result = client.post(f"/api/lessons/{lesson['id']}/homework/draft", json={})
    assert result.status_code == 503
    assert result.json()["detail"] == {"code": "missing_api_key"}
    assert client.post(f"/api/students/{student['id']}/lesson-plan", json={"topic": "Тема", "duration_minutes": 0}).status_code == 422
    assert client.post(f"/api/lessons/{lesson['id']}/feedback/draft", json={"recipient": "stranger"}).status_code == 422
    assert client.put(f"/api/lessons/{lesson['id']}/homework", json={"homework": " "}).status_code == 422
    assert client.post("/api/lessons/00000000-0000-0000-0000-000000000001/homework/draft", json={}).status_code == 404
