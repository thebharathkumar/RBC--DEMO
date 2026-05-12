"""Pytest configuration shared across the API test suite."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the test process into a predictable environment.

    Tests run under APP_ENV=test with empty credentials so we never accidentally
    hit a real upstream from a unit test.
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
    # Avoid leaking parent-shell env file overrides into pydantic-settings.
    os.environ.pop("ENV_FILE", None)
