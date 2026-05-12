"""Typed application settings loaded from environment variables.

Pydantic settings give us a single typed surface for configuration so agents,
adapters, and middleware never read raw os.environ. Validators reject obviously
broken production configurations at boot rather than producing degraded runs.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    app_version: str = "0.1.0"

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Origins permitted to call the API. Empty disables CORS.",
    )

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

    @model_validator(mode="after")
    def _enforce_production_preconditions(self) -> Settings:
        # Boot-time guard so a misconfigured prod deploy fails loudly rather
        # than silently degrading to unauthenticated upstream calls.
        if self.app_env == "production":
            missing: list[str] = []
            if not self.anthropic_api_key.get_secret_value():
                missing.append("ANTHROPIC_API_KEY")
            if "contact@example.invalid" in self.sec_edgar_user_agent:
                missing.append("SEC_EDGAR_USER_AGENT")
            if missing:
                raise ValueError(
                    "production environment missing required configuration: " + ", ".join(missing)
                )
        return self

    @model_validator(mode="after")
    def _normalize_log_level(self) -> Settings:
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        normalized = self.app_log_level.upper()
        if normalized not in allowed:
            raise ValueError(f"app_log_level must be one of {sorted(allowed)}")
        object.__setattr__(self, "app_log_level", normalized)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached Settings instance. Useful in tests after env changes."""

    get_settings.cache_clear()
