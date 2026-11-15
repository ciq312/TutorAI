import asyncio
import json

import httpx
import pytest

from app.core.config import Settings
from app.rag.embeddings import EmbeddingError, GeminiEmbeddings, validate_vectors
from app.rag.text import chunks
from app.privacy.people import PersonIdentity, PersonRef
from app.privacy.text import TextAnonymizer
from uuid import UUID


def settings():
    return Settings(database_url="postgresql://a:b@localhost/test", gemini_api_key="secret", embedding_dimensions=3)


def test_gemini_contract_and_normalization():
    def handler(request):
        assert request.headers["x-goog-api-key"] == "secret"
        assert "secret" not in str(request.url)
        assert request.url.path.endswith("/gemini-embedding-001:batchEmbedContents")
        body = json.loads(request.content)
        assert len(body["requests"]) == 2
        assert body["requests"][0] == {
            "model": "models/gemini-embedding-001", "content": {"parts": [{"text": "first"}]},
            "taskType": "RETRIEVAL_DOCUMENT", "outputDimensionality": 3,
        }
        return httpx.Response(200, json={"embeddings": [{"values": [3, 4, 0]}, {"values": [0, 1, 0]}]})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await GeminiEmbeddings(settings(), client).embed(["first", "second"], "RETRIEVAL_DOCUMENT")
            assert result == [[0.6, 0.8, 0], [0, 1, 0]]
    asyncio.run(run())


@pytest.mark.parametrize("status,code", [(429, "rate_limited"), (403, "provider_access_denied"), (500, "provider_error")])
def test_safe_errors(status, code):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text="secret and personal data"),
        )) as client:
            with pytest.raises(EmbeddingError, match=f"^{code}$"):
                await GeminiEmbeddings(settings(), client).embed(["private"], "RETRIEVAL_QUERY")
    asyncio.run(run())


@pytest.mark.parametrize("vectors", [[], [[1, 2]], [[0, 0, 0]], [[float('nan'), 1, 2]], [[True, 1, 2]]])
def test_invalid_vectors(vectors):
    with pytest.raises(EmbeddingError):
        validate_vectors(vectors, 1, 3)


def test_redaction_and_chunk_coverage():
    anonymizer = TextAnonymizer((PersonIdentity(PersonRef("student", UUID(int=1)), "Анна"),))
    assert anonymizer.prepare("Анна: anna@example.com +375 (29) 123-45-67") == "[имя]: [email] [телефон]"
    text = "Тема: " + "длинная история " * 500
    parts = chunks(text)
    assert all(len(part) <= 1800 for part in parts)
    assert len(parts) > 1
    assert parts[0] + "".join(part[200:] for part in parts[1:]) == text
