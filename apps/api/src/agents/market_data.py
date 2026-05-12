"""MarketDataAnalyst worker.

Pulls a price history, projects it into a ``MarketSnapshot``, and packages it
as a typed ``WorkerResult``. The worker performs no LLM call; the market block
is a deterministic projection from price data and must remain so.
"""

from __future__ import annotations

import time

from src.data.market import MarketDataAdapter
from src.models.state import (
    AgentError,
    AgentName,
    ResearchState,
    WorkerResult,
    WorkerStatus,
)


class MarketDataAnalyst:
    name = AgentName.MARKET_DATA

    def __init__(self, adapter: MarketDataAdapter | None = None) -> None:
        self._adapter = adapter or MarketDataAdapter()

    def run(self, state: ResearchState) -> dict[AgentName, WorkerResult]:
        started = time.perf_counter()
        try:
            snapshot, citation = self._adapter.snapshot(state.ticker)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return {
                self.name: WorkerResult(
                    agent=self.name,
                    status=WorkerStatus.UNAVAILABLE,
                    latency_ms=latency_ms,
                    error=AgentError(
                        type=type(exc).__name__,
                        message=str(exc)[:500],
                        agent=self.name,
                    ),
                )
            }

        latency_ms = (time.perf_counter() - started) * 1000
        return {
            self.name: WorkerResult(
                agent=self.name,
                status=WorkerStatus.OK,
                data={"snapshot": snapshot.model_dump()},
                citations=(citation,),
                latency_ms=latency_ms,
            )
        }
