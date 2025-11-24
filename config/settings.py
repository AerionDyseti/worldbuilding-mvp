"""Project-wide settings management via Pydantic BaseSettings."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Resonance services."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="RESONANCE_")

    data_dir: Path = Path("./data")
    sqlite_path: Path = Path("./data/resonance.db")

    # Embeddings / vector search
    embedding_model: str = "local-stub"
    embedding_dimension: int = 64

    # OpenRouter / LLM extraction
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "openrouter/anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    extraction_max_tokens: int = 2000

    # Misc
    request_timeout_seconds: int = 60


def get_settings() -> Settings:
    """Provide a cached settings instance."""

    # Pydantic BaseSettings caches instances by default, so this is simple.
    return Settings()
