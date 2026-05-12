"""Tests for the LLMClient mock mode and cost accounting."""

from __future__ import annotations

import json

import pytest

from src.agents.llm import LLMClient, LLMResponse


def test_mock_mode_is_engaged_when_no_api_key() -> None:
    client = LLMClient(api_key=None)
    assert client.is_mocked


def test_mock_complete_returns_valid_json() -> None:
    client = LLMClient(mock=True)
    response = client.complete(system="s", user="u")
    payload = response.parsed_json()
    assert "executive_summary" in payload
    assert isinstance(payload["investment_theses"], list)


def test_mock_response_can_be_injected() -> None:
    body = json.dumps({"executive_summary": "x", "investment_theses": []})
    client = LLMClient(mock=True, mock_response=body)
    response = client.complete(system="s", user="u")
    assert response.parsed_json()["executive_summary"] == "x"


def test_cost_breakdown_uses_pricing_table() -> None:
    response = LLMResponse(
        content="{}",
        model="claude-sonnet-4-6",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    cost = response.cost
    assert cost.usd == pytest.approx(18.0)


def test_cost_for_unknown_model_is_zero() -> None:
    response = LLMResponse(
        content="{}",
        model="unknown-model",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert response.cost.usd == 0.0


def test_parse_json_strips_surrounding_prose() -> None:
    response = LLMResponse(
        content='Here you go: {"key": 1} done.',
        model="claude-sonnet-4-6",
        input_tokens=1,
        output_tokens=1,
    )
    assert response.parsed_json() == {"key": 1}


def test_parse_json_raises_on_no_object() -> None:
    response = LLMResponse(
        content="no json here",
        model="claude-sonnet-4-6",
        input_tokens=1,
        output_tokens=1,
    )
    with pytest.raises(ValueError):
        response.parsed_json()
