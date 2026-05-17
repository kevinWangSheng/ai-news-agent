"""Centralized settings — all tunables live here (per 001-Task 5a / C1)."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://hub:hub@localhost:5432/hub"

    anthropic_api_key: str | None = None
    voyage_api_key: str | None = None
    openai_api_key: str | None = None
    ark_api_key: str | None = None
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3"
    ark_embed_model: str = "doubao-embedding-vision"
    exa_api_key: str | None = None
    twitter_bearer_token: str | None = None

    exclude_keywords: list[str] = Field(default_factory=list)
    focus_keywords: list[str] = Field(default_factory=list)

    scoring_inbox_threshold: float = 6.0
    scoring_breaking_threshold: float = 5.0
    digest_score_threshold: float = 7.0
    preference_cold_start_min_interactions: int = 50

    hnsw_m: int = 16
    hnsw_ef_construction: int = 64

    processing_max_attempts: int = 3
    processing_concurrency: int = 4

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
