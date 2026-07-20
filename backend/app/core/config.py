from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "AI YouTube Summarizer"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_summarizer"

    # --- Redis (caching, Celery broker/backend, rate limiting) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Vector store ---
    VECTOR_STORE_PROVIDER: Literal["chroma", "pinecone"] = "chroma"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str | None = None

    # --- LLM providers (all configurable; LLM_PROVIDER selects the active one) ---
    LLM_PROVIDER: Literal["claude", "openai", "gemini", "openrouter"] = "claude"

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"

    GOOGLE_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # OpenRouter: OpenAI-API-compatible, but a distinct provider/base URL/key
    # from plain OpenAI — routes to whichever free/paid model OPENROUTER_MODEL
    # names (e.g. "meta-llama/llama-3.3-70b-instruct:free").
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "nvidia/nemotron-nano-9b-v2:free"

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Auth ---
    JWT_SECRET_KEY: str = "changeme-generate-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_OAUTH_CLIENT_ID: str | None = None
    GOOGLE_OAUTH_CLIENT_SECRET: str | None = None

    # --- YouTube ---
    YOUTUBE_API_KEY: str | None = None

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 30

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance, so env parsing happens once per process."""
    return Settings()
