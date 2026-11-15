"""LLM adapters. Provider errors never expose input, keys or response bodies."""
from typing import Protocol

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings


class LLMError(Exception):
    pass


class LLMProvider(Protocol):
    async def generate(self, system: str, prompt: str, schema: type[BaseModel]) -> BaseModel: ...


class HTTPModel:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client

    async def generate(self, system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        config = self.settings
        if config.llm_provider == "gemini":
            key = config.gemini_api_key.get_secret_value()
            if not key:
                raise LLMError("missing_api_key")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.llm_model}:generateContent"
            headers = {"x-goog-api-key": key}
            body = {"systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json",
                                         "responseJsonSchema": schema.model_json_schema(),
                                         "maxOutputTokens": 8192}}
            if config.llm_model.startswith("gemini-3"):
                body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "low"}
        else:
            url = f"{config.ollama_base_url.rstrip('/')}/api/chat"
            headers = {}
            body = {"model": config.llm_model, "stream": False,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": prompt}],
                    "format": schema.model_json_schema(), "options": {"num_predict": 8192}}
        try:
            response = await self.client.post(url, headers=headers, json=body)
        except httpx.TimeoutException:
            raise LLMError("provider_timeout") from None
        except httpx.RequestError:
            raise LLMError("provider_unavailable") from None
        if not response.is_success:
            code = {429: "rate_limited", 401: "provider_access_denied", 403: "provider_access_denied"}.get(response.status_code, "provider_error")
            raise LLMError(code)
        try:
            data = response.json()
            if config.llm_provider == "gemini":
                candidate = data["candidates"][0]
                if candidate.get("finishReason") != "STOP":
                    raise LLMError("incomplete_response")
                content = "".join(part.get("text", "") for part in candidate["content"]["parts"])
            else:
                if not data.get("done") or data.get("done_reason") == "length":
                    raise LLMError("incomplete_response")
                content = data["message"]["content"]
            return schema.model_validate_json(content)
        except (KeyError, IndexError, TypeError, ValueError, ValidationError):
            raise LLMError("invalid_response") from None


def build_llm(settings: Settings, client: httpx.AsyncClient) -> LLMProvider:
    return HTTPModel(settings, client)
