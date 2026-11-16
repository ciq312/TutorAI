from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    embedding_provider: Literal["gemini"] = "gemini"
    embedding_model: str = Field(default="gemini-embedding-001", pattern=r"^[a-zA-Z0-9._-]+$")
    embedding_dimensions: int = Field(default=768, ge=1, le=3072)
    embedding_timeout: float = Field(default=30, gt=0, le=120)
    gemini_api_key: SecretStr = SecretStr("")
    llm_provider: Literal["gemini", "ollama"] = "gemini"
    llm_model: str = Field(default="gemini-3.8-flash", pattern=r"^[a-zA-Z0-9._:-]+$")
    llm_timeout: float = Field(default=180, gt=0, le=300)
    ollama_base_url: str = "http://localhost:11434"
    debug: bool = False
    app_name: str = "Tutor RAG"
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://localhost:8000/api/integrations/google/callback"
    integration_encryption_key: SecretStr = SecretStr("")
    telegram_bot_token: SecretStr = SecretStr("")
    public_app_url: str = "http://localhost:5173"
    worker_interval_seconds: int = Field(default=30, ge=5, le=300)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("database_url")
    @classmethod
    def async_database_url(cls, value: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return value.replace(prefix, "postgresql+asyncpg://", 1)
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use PostgreSQL with asyncpg")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
