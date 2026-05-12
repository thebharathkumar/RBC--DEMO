"""Synthesizer agent.

Consumes the worker outputs and produces a ``NoteDraft``. Calls the LLM in
JSON mode (by prompt contract) and validates the response against the
schema. Returns the draft as a free-form dict so the LangGraph reducer can
write it back into ``ResearchState.note``.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import ValidationError

from src.agents.llm import LLMClient
from src.models.note import Claim, MarketSnapshot, NoteDraft
from src.models.state import (
    AgentError,
    AgentName,
    CostBreakdown,
    ResearchState,
    SourceCitation,
    WorkerResult,
    WorkerStatus,
)

_SYSTEM_PROMPT = """You are a senior sell-side equity research associate.

You will be given a structured JSON blob of analytics for a single ticker.
Produce a research note as a single JSON object with this exact schema:

{
  "executive_summary": "<3 sentences>",
  "investment_theses": [
    {"statement": "<one thesis>", "citation_ids": ["<source_id>", ...]}
  ],
  "key_risks": [
    {"statement": "<one risk>", "citation_ids": ["<source_id>", ...]}
  ],
  "catalysts": [
    {"statement": "<one catalyst>", "citation_ids": ["<source_id>", ...]}
  ]
}

Rules:
- Produce exactly three theses, three risks, and three catalysts unless the
  inputs do not support that many. Better to produce fewer with citations
  than to fabricate.
- Every statement must reference at least one citation_id taken verbatim
  from the source_ids supplied in the input.
- No marketing language. No hedging filler. No em dashes.
- Output a single JSON object and nothing else.
"""


class Synthesizer:
    name = AgentName.SYNTHESIZER

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def run(self, state: ResearchState) -> dict[str, Any]:
        started = time.perf_counter()
        user = _build_user_prompt(state)
        citation_index = {c.source_id: c for c in state.all_citations()}

        try:
            response = self._llm.complete(system=_SYSTEM_PROMPT, user=user)
            payload = response.parsed_json()
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return {
                "worker_results": {
                    self.name: WorkerResult(
                        agent=self.name,
                        status=WorkerStatus.ERROR,
                        latency_ms=latency_ms,
                        error=AgentError(
                            type=type(exc).__name__,
                            message=str(exc)[:500],
                            agent=self.name,
                        ),
                    )
                }
            }

        try:
            draft = _materialise_draft(state, payload, citation_index)
        except ValidationError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return {
                "worker_results": {
                    self.name: WorkerResult(
                        agent=self.name,
                        status=WorkerStatus.ERROR,
                        latency_ms=latency_ms,
                        error=AgentError(
                            type="schema_validation",
                            message=str(exc)[:500],
                            agent=self.name,
                        ),
                    )
                }
            }

        latency_ms = (time.perf_counter() - started) * 1000
        cost = response.cost
        return {
            "worker_results": {
                self.name: WorkerResult(
                    agent=self.name,
                    status=WorkerStatus.OK,
                    latency_ms=latency_ms,
                    cost=cost,
                )
            },
            "note": draft.model_dump(),
        }


def _build_user_prompt(state: ResearchState) -> str:
    sources: list[dict[str, str]] = []
    workers: dict[str, dict[str, Any]] = {}
    for name, result in state.worker_results.items():
        if name == AgentName.SYNTHESIZER:
            continue
        workers[name.value] = {
            "status": result.status.value,
            "data": result.data,
            "source_ids": [c.source_id for c in result.citations],
        }
        sources.extend({"source_id": c.source_id, "locator": c.locator} for c in result.citations)

    payload = {
        "ticker": state.ticker,
        "available_sources": sources,
        "worker_outputs": workers,
    }
    return "Inputs follow as a JSON object. Produce the note JSON as specified.\n" + json.dumps(
        payload, separators=(",", ":"), sort_keys=True
    )


def _materialise_draft(
    state: ResearchState,
    payload: dict[str, Any],
    citation_index: dict[str, SourceCitation],
) -> NoteDraft:
    snapshot_data = state.worker_results.get(AgentName.MARKET_DATA)
    snapshot = None
    if snapshot_data is not None and snapshot_data.status == WorkerStatus.OK:
        snapshot = MarketSnapshot(**snapshot_data.data.get("snapshot", {}))

    return NoteDraft(
        ticker=state.ticker,
        executive_summary=str(payload.get("executive_summary", "")).strip(),
        investment_theses=tuple(
            _build_claim(item, citation_index) for item in payload.get("investment_theses", [])
        ),
        key_risks=tuple(
            _build_claim(item, citation_index) for item in payload.get("key_risks", [])
        ),
        catalysts=tuple(
            _build_claim(item, citation_index) for item in payload.get("catalysts", [])
        ),
        market_snapshot=snapshot,
    )


def _build_claim(item: dict[str, Any], citation_index: dict[str, SourceCitation]) -> Claim:
    raw_ids = item.get("citation_ids", []) or item.get("citations", [])
    citations = tuple(citation_index[sid] for sid in raw_ids if sid in citation_index)
    return Claim(statement=str(item.get("statement", "")).strip(), citations=citations)


# Pricing accessors so an outer trace span can read the cost when needed.
def synthesizer_cost(state: ResearchState) -> CostBreakdown:
    result = state.worker_results.get(AgentName.SYNTHESIZER)
    return result.cost if result is not None else CostBreakdown()
