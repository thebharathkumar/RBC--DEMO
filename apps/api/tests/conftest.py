"""Pytest configuration shared across the API test suite."""

from __future__ import annotations

import os

import pytest

from src.config import reset_settings_cache


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the test process into a predictable environment.

    Tests run under APP_ENV=test with empty credentials so we never accidentally
    hit a real upstream from a unit test. The settings cache is cleared so the
    overrides actually take effect; ``lru_cache`` is otherwise process-wide.
    """

    monkeypatch.setenv("APP_ENV", "test")
    for key in (
        "ANTHROPIC_API_KEY",
        "POLYGON_API_KEY",
        "TAVILY_API_KEY",
        "NEWSAPI_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
    ):
        monkeypatch.setenv(key, "")
    os.environ.pop("ENV_FILE", None)
    reset_settings_cache()
    yield
    reset_settings_cache()
