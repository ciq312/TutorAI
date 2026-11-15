import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import DocumentChunk
from app.rag.embeddings import EmbeddingError
from app.services.context import get_provider
from tests.test_api import student, lesson


class FakeEmbeddings:
    identity = "fake/model-a"
    dimensions = 3

    def __init__(self):
        self.error = None
        self.calls = []

    async def embed(self, texts, task):
        self.calls.append((texts, task))
        if self.error:
            raise EmbeddingError(self.error)
        return [[1, 0, 0] if any(x in text.lower() for x in ("знак", "минус", "скоб"))
                else [0, 1, 0] for text in texts]


def setup(client):
    provider = FakeEmbeddings()
    client.app.dependency_overrides[get_provider] = lambda: provider
    return provider


def search(client, sid, **kwargs):
    response = client.post(f"/api/students/{sid}/context/search", json={"query": "ошибки со знаками", **kwargs})
    assert response.status_code == 200, response.text
    return response.json()


def count_chunks(database_url):
    async def run():
        engine = create_async_engine(database_url)
        try:
            async with engine.connect() as connection:
                return await connection.scalar(select(func.count()).select_from(DocumentChunk))
        finally:
            await engine.dispose()
    return asyncio.run(run())


def test_semantics_chronology_dates_isolation_and_dedup(client):
    provider = setup(client)
    sid, other = student(client), student(client, "Борис")
    old = lesson(client, sid, "2026-10-01T12:00:00Z", topic="Раскрытие скобок", notes="Теряет минус")
    new = lesson(client, sid, "2026-11-01T12:00:00Z", topic="Геометрия")
    foreign = lesson(client, other, notes="Теряет минус")
    result = search(client, sid, recent_lessons_limit=1)
    assert [x["lesson_id"] for x in result["sources"]] == [new["id"], old["id"]]
    assert result["sources"][1]["reasons"] == ["semantic"]
    assert foreign["id"] not in str(result)
    assert result["unindexed_lessons"] == 0
    merged = search(client, sid, recent_lessons_limit=2)
    assert merged["sources"][1]["reasons"] == ["recent", "semantic"]
    filtered = search(client, sid, date_from="2026-11-01T12:00:00Z", date_to="2026-11-01T12:00:00Z")
    assert [x["lesson_id"] for x in filtered["sources"]] == [new["id"]]
    assert provider.calls[-1][1] == "RETRIEVAL_QUERY"


def test_update_failure_retry_delete_and_cascade(client, database_url):
    provider = setup(client)
    sid = student(client)
    entry = lesson(client, sid, notes="Теряет минус")
    assert entry["indexing_status"] == "ready"
    assert count_chunks(database_url) == 1
    provider.error = "rate_limited"
    updated = client.patch(f"/api/lessons/{entry['id']}", json={"notes": "Геометрия"}).json()
    assert updated["notes"] == "Геометрия"
    assert updated["indexing_status"] == "failed"
    assert updated["indexing_error"] == "rate_limited"
    assert count_chunks(database_url) == 0
    result = search(client, sid, recent_lessons_limit=0)
    assert result["sources"] == [] and result["unindexed_lessons"] == 1
    assert "index_incomplete" in result["warnings"]
    provider.error = None
    assert client.post(f"/api/lessons/{entry['id']}/index").json()["indexing_status"] == "ready"
    assert count_chunks(database_url) == 1
    assert client.delete(f"/api/lessons/{entry['id']}").status_code == 204
    assert count_chunks(database_url) == 0
    lesson(client, sid)
    assert client.delete(f"/api/students/{sid}").status_code == 204
    assert count_chunks(database_url) == 0


def test_provider_failure_and_model_switch(client):
    provider = setup(client)
    sid = student(client)
    lesson(client, sid, notes="Теряет минус")
    provider.error = "provider_timeout"
    degraded = search(client, sid)
    assert degraded["semantic_status"] == "unavailable"
    assert len(degraded["sources"]) == 1
    provider.error = None
    provider.identity = "fake/model-b"
    provider.dimensions = 2
    incompatible = search(client, sid, recent_lessons_limit=0)
    assert incompatible["sources"] == []
    assert incompatible["unindexed_lessons"] == 1


def test_empty_redaction_bounds_and_validation(client):
    provider = setup(client)
    sid = student(client)
    assert search(client, sid)["semantic_status"] == "empty"
    assert provider.calls == []
    client.post(f"/api/students/{sid}/contacts", json={"name": "Мария", "phone": "+12025550101"})
    entry = lesson(client, sid, notes="Анна и Мария, anna@example.com +12025550101 " + "текст " * 1000)
    sent = str(provider.calls)
    for private in ("Анна", "Мария", "anna@example.com", "+12025550101"):
        assert private not in sent
    result = search(client, sid, query="Анна +12025550101", max_context_chars=500)
    assert sum(len(t) for s in result["sources"] for t in s["excerpts"]) <= 500
    assert "context_truncated" in result["warnings"]
    before = len(provider.calls)
    client.patch(f"/api/lessons/{entry['id']}", json={"scheduled_at": "2026-12-01T12:00:00Z"})
    assert len(provider.calls) == before
    path = f"/api/students/{sid}/context/search"
    for payload in ({"query": " "}, {"query": "x", "semantic_limit": 30},
                    {"query": "x", "date_from": "2026-11-01T00:00:00"},
                    {"query": "x", "date_from": "2026-12-01T00:00:00Z", "date_to": "2026-11-01T00:00:00Z"}):
        assert client.post(path, json=payload).status_code == 422


def test_reindex_command_retries_and_skips_ready(client, database_url, monkeypatch):
    import app.reindex as command
    from app.core.config import Settings

    provider = setup(client)
    provider.error = "rate_limited"
    sid = student(client)
    entry = lesson(client, sid, notes="Теряет минус")
    monkeypatch.setattr(command, "get_settings", lambda: Settings(database_url=database_url, gemini_api_key=""))
    monkeypatch.setattr(command, "build_provider", lambda config, http: provider)
    assert asyncio.run(command.reindex()) == {"ready": 0, "failed": 1}
    provider.error = None
    assert asyncio.run(command.reindex()) == {"ready": 1, "failed": 0}
    calls = len(provider.calls)
    assert asyncio.run(command.reindex()) == {"ready": 0, "failed": 0}
    assert len(provider.calls) == calls
    provider.identity = "fake/model-b"
    assert asyncio.run(command.reindex()) == {"ready": 1, "failed": 0}
    assert client.get(f"/api/lessons/{entry['id']}").json()["indexing_status"] == "ready"


def test_evaluation_command_reports_real_sources(client, database_url, monkeypatch, tmp_path):
    import json
    import app.evaluate_retrieval as command
    from app.core.config import Settings

    provider = setup(client)
    sid = student(client)
    entry = lesson(client, sid, notes="Теряет минус")
    lesson(client, sid, topic="Геометрия")
    monkeypatch.setattr(command, "get_settings", lambda: Settings(database_url=database_url, gemini_api_key=""))
    monkeypatch.setattr(command, "build_provider", lambda config, http: provider)
    path = tmp_path / "eval.json"
    path.write_text(json.dumps({"cases": [{"student_id": sid, "query": "ошибки со знаками",
                                          "expected_lesson_ids": [entry["id"]]}]}))
    results = asyncio.run(command.evaluate(path))
    assert results[0]["recall_at_5"] == 1
    assert results[0]["precision_at_5"] == 1
    assert results[0]["warnings"] == []
