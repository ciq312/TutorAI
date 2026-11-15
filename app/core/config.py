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
    debug: bool = False
    app_name: str = "Tutor RAG"

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
