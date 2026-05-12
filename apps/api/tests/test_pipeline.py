"""End-to-end tests for the LangGraph pipeline.

A fake price fetcher and the LLM mock mode together let us run the full graph
in CI without any network or API key.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.agents.llm import LLMClient
from src.agents.market_data import MarketDataAnalyst
from src.agents.synthesizer import Synthesizer
from src.data.market import MarketDataAdapter, PriceFetcher, PriceSeries
from src.graph.builder import run_pipeline
from src.main import create_app
from src.models.state import AgentName, WorkerStatus


class _FakeFetcher(PriceFetcher):
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, ticker: str, *, days: int) -> PriceSeries:
        self.calls += 1
        start = datetime(2025, 1, 1, tzinfo=UTC)
        closes = tuple(100.0 + i * 0.05 for i in range(280))
        timestamps = tuple(start + timedelta(days=i) for i in range(280))
        return PriceSeries(ticker=ticker, timestamps=timestamps, closes=closes)


def _mock_note_body() -> str:
    return json.dumps(
        {
            "executive_summary": "Three-sentence summary built from a deterministic fake price series.",
            "investment_theses": [
                {
                    "statement": "Realised volatility sits in line with the 1Y average.",
                    "citation_ids": ["yfinance:AAPL"],
                }
            ],
            "key_risks": [
                {
                    "statement": "Drawdown discipline could deteriorate in a rate shock.",
                    "citation_ids": ["yfinance:AAPL"],
                }
            ],
            "catalysts": [
                {
                    "statement": "Next earnings print expected within 60 days.",
                    "citation_ids": ["yfinance:AAPL"],
                }
            ],
        }
    )


def test_pipeline_runs_end_to_end_with_mocks() -> None:
    fetcher = _FakeFetcher()
    adapter = MarketDataAdapter(fetcher=fetcher)
    market_data = MarketDataAnalyst(adapter=adapter)
    synthesizer = Synthesizer(
        llm=LLMClient(mock=True, mock_response=_mock_note_body()),
    )

    state = run_pipeline("AAPL", market_data=market_data, synthesizer=synthesizer)

    assert fetcher.calls == 1
    assert AgentName.MARKET_DATA in state.worker_results
    assert AgentName.SYNTHESIZER in state.worker_results
    assert state.worker_results[AgentName.MARKET_DATA].status == WorkerStatus.OK
    assert state.worker_results[AgentName.SYNTHESIZER].status == WorkerStatus.OK
    assert state.note is not None
    assert state.note["ticker"] == "AAPL"
    assert len(state.note["investment_theses"]) >= 1
    # Every thesis must be cited; the mock note cites yfinance:AAPL.
    for claim in state.note["investment_theses"]:
        assert len(claim["citations"]) >= 1
    assert state.all_citations()
    assert state.total_cost().usd >= 0.0


def test_pipeline_records_error_when_fetcher_fails() -> None:
    class _BrokenFetcher(PriceFetcher):
        def fetch(self, ticker: str, *, days: int) -> PriceSeries:
            raise RuntimeError("upstream down")

    state = run_pipeline(
        "AAPL",
        market_data=MarketDataAnalyst(adapter=MarketDataAdapter(fetcher=_BrokenFetcher())),
        synthesizer=Synthesizer(llm=LLMClient(mock=True)),
    )

    market = state.worker_results[AgentName.MARKET_DATA]
    assert market.status == WorkerStatus.UNAVAILABLE
    assert market.error is not None
    assert "upstream down" in market.error.message


def test_create_run_route_returns_summary() -> None:
    client = TestClient(create_app())
    response = client.post("/runs", json={"ticker": "AAPL"})
    assert response.status_code == 201, response.text
    summary = response.json()
    assert summary["ticker"] == "AAPL"
    assert summary["worker_count"] >= 1
    run_id = summary["run_id"]

    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["ticker"] == "AAPL"
    assert body["worker_results"]


def test_get_run_returns_404_for_unknown_id() -> None:
    client = TestClient(create_app())
    response = client.get("/runs/00000000000000000000")
    assert response.status_code == 404
