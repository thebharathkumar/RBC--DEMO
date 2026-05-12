"""Tests for boot-time configuration validators."""

from __future__ import annotations

import pytest

from src.config import Settings, reset_settings_cache


def test_log_level_is_normalized() -> None:
    settings = Settings(app_log_level="debug")
    assert settings.app_log_level == "DEBUG"


def test_log_level_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        Settings(app_log_level="loud")


def test_production_requires_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "rbc bharath.kr702@gmail.com")
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        Settings()


def test_production_requires_real_edgar_user_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_settings_cache()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-not-real")
    monkeypatch.setenv(
        "SEC_EDGAR_USER_AGENT",
        "rbc-research-agent-platform contact@example.invalid",
    )
    with pytest.raises(ValueError, match="SEC_EDGAR_USER_AGENT"):
        Settings()


def test_development_defaults_are_permissive() -> None:
    settings = Settings(app_env="development")
    assert settings.app_env == "development"
    assert settings.enable_prompt_injection_guard is True
