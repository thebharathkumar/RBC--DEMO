"""Tests for ResearchState and supporting models."""

from __future__ import annotations

import pytest

from src.models.state import (
    AgentName,
    CostBreakdown,
    ResearchState,
    SourceCitation,
    WorkerResult,
    WorkerStatus,
)


def test_ticker_is_normalised_and_validated() -> None:
    state = ResearchState(ticker="  aapl  ")
    assert state.ticker == "AAPL"


@pytest.mark.parametrize("bad", ["", " ", "!!", "TOOOOOLONGTICKER"])
def test_ticker_rejects_invalid(bad: str) -> None:
    with pytest.raises(ValueError):
        ResearchState(ticker=bad)


def test_citation_hash_is_content_addressed() -> None:
    c1 = SourceCitation.for_payload(source_id="edgar:0001", payload="hello")
    c2 = SourceCitation.for_payload(source_id="edgar:0001", payload="hello")
    c3 = SourceCitation.for_payload(source_id="edgar:0001", payload="world")
    assert c1.hash == c2.hash
    assert c1.hash != c3.hash
    assert len(c1.hash) == 64


def test_citation_rejects_non_hex_hash() -> None:
    with pytest.raises(ValueError):
        SourceCitation(source_id="x", hash="z" * 64)


def test_total_cost_sums_across_workers() -> None:
    state = ResearchState(
        ticker="AAPL",
        worker_results={
            AgentName.MARKET_DATA: WorkerResult(
                agent=AgentName.MARKET_DATA,
                status=WorkerStatus.OK,
                cost=CostBreakdown(input_tokens=10, output_tokens=20, usd=0.001),
            ),
            AgentName.SYNTHESIZER: WorkerResult(
                agent=AgentName.SYNTHESIZER,
                status=WorkerStatus.OK,
                cost=CostBreakdown(input_tokens=100, output_tokens=200, usd=0.01),
            ),
        },
    )
    total = state.total_cost()
    assert total.input_tokens == 110
    assert total.output_tokens == 220
    assert total.usd == pytest.approx(0.011)


def test_all_citations_returns_flattened_tuple() -> None:
    cite_a = SourceCitation.for_payload(source_id="a", payload="x")
    cite_b = SourceCitation.for_payload(source_id="b", payload="y")
    state = ResearchState(
        ticker="MSFT",
        worker_results={
            AgentName.MARKET_DATA: WorkerResult(
                agent=AgentName.MARKET_DATA,
                status=WorkerStatus.OK,
                citations=(cite_a, cite_b),
            ),
        },
    )
    assert state.all_citations() == (cite_a, cite_b)
