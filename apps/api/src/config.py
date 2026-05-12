"""Typed application settings loaded from environment variables.

Pydantic settings give us a single typed surface for configuration so agents,
adapters, and middleware never read raw os.environ.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_log_level: str = "INFO"
    app_port: int = 8000

    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model_synthesis: str = "claude-sonnet-4-6"
    anthropic_model_extraction: str = "claude-haiku-4-5-20251001"

    database_url: str = "postgresql+asyncpg://rbc:rbc@localhost:5432/rbc_research"
    redis_url: str = "redis://localhost:6379/0"

    sec_edgar_user_agent: str = Field(
        default="rbc-research-agent-platform contact@example.invalid",
        description="EDGAR requires a contact UA string for all requests.",
    )
    polygon_api_key: SecretStr = SecretStr("")
    tavily_api_key: SecretStr = SecretStr("")
    newsapi_api_key: SecretStr = SecretStr("")

    langfuse_public_key: SecretStr = SecretStr("")
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "https://cloud.langfuse.com"

    enable_human_review_gate: bool = False
    enable_prompt_injection_guard: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
