"""Replaceable embeddings contract; no provider types escape this module."""
import math
from typing import Literal, Protocol

import httpx

from app.core.config import Settings

Task = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


class EmbeddingError(Exception):
    """Safe error code only: never retain provider bodies, keys or input text."""


class EmbeddingProvider(Protocol):
    identity: str
    dimensions: int

    async def embed(self, texts: list[str], task: Task) -> list[list[float]]: ...


def validate_vectors(vectors, count: int, dimensions: int) -> list[list[float]]:
    if not isinstance(vectors, list) or len(vectors) != count:
        raise EmbeddingError("invalid_response")
    result = []
    for vector in vectors:
        if not isinstance(vector, list) or len(vector) != dimensions:
            raise EmbeddingError("invalid_dimensions")
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
            raise EmbeddingError("invalid_vector")
        norm = math.hypot(*vector)
        if not norm or not math.isfinite(norm):
            raise EmbeddingError("invalid_vector")
        result.append([x / norm for x in vector])
    return result


class GeminiEmbeddings:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.model = settings.embedding_model
        self.identity = f"gemini/{self.model}"
        self.dimensions = settings.embedding_dimensions
        self.key = settings.gemini_api_key.get_secret_value()
        self.client = client

    async def embed(self, texts: list[str], task: Task) -> list[list[float]]:
        if not self.key:
            raise EmbeddingError("missing_api_key")
        if not texts:
            return []
        try:
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:batchEmbedContents",
                headers={"x-goog-api-key": self.key},
                json={"requests": [
                    {"model": f"models/{self.model}", "content": {"parts": [{"text": text}]},
                     "taskType": task, "outputDimensionality": self.dimensions}
                    for text in texts
                ]},
            )
        except httpx.TimeoutException:
            raise EmbeddingError("provider_timeout") from None
        except httpx.RequestError:
            raise EmbeddingError("provider_unavailable") from None
        if response.status_code == 429:
            raise EmbeddingError("rate_limited")
        if response.status_code in (401, 403):
            raise EmbeddingError("provider_access_denied")
        if not response.is_success:
            raise EmbeddingError("provider_error")
        try:
            vectors = [item["values"] for item in response.json()["embeddings"]]
        except (ValueError, KeyError, TypeError):
            raise EmbeddingError("invalid_response") from None
        return validate_vectors(vectors, len(texts), self.dimensions)


def build_provider(settings: Settings, client: httpx.AsyncClient) -> EmbeddingProvider:
    # New adapters are selected here; indexing and retrieval use only the protocol.
    if settings.embedding_provider == "gemini":
        return GeminiEmbeddings(settings, client)
    raise ValueError("Unsupported embedding provider")
