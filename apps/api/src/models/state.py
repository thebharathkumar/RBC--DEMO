"""Typed state that flows through the LangGraph supervisor.

This is the single source of truth for what an agent may read and write. Every
worker receives the full state but is restricted by convention (and by the
LangGraph reducer below) to filling its own slot.

The state is content-addressed: every retrieved source carries a hash, and
the final note carries a hash of the inputs that produced it. That hash chain
is what makes the run auditable.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_run_id() -> str:
    return uuid4().hex


class AgentName(StrEnum):
    SUPERVISOR = "supervisor"
    FILINGS = "filings"
    EARNINGS = "earnings"
    MARKET_DATA = "market_data"
    NEWS = "news"
    COMPARABLES = "comparables"
    CRITIQUE = "critique"
    SYNTHESIZER = "synthesizer"


class WorkerStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class SourceCitation(BaseModel):
    """Pointer to a retrieved artifact.

    ``source_id`` is the human-readable identifier (e.g. an EDGAR accession
    or a yfinance reference). ``hash`` is a SHA-256 over the raw payload the
    agent actually consumed, so a downstream auditor can verify the agent did
    not reason over a different document than the one cited.
    """

    model_config = ConfigDict(frozen=True)

    source_id: str
    hash: str = Field(min_length=64, max_length=64)
    locator: str = ""

    @field_validator("hash")
    @classmethod
    def _validate_hash(cls, v: str) -> str:
        int(v, 16)  # raises if not hex
        return v

    @classmethod
    def for_payload(
        cls, *, source_id: str, payload: bytes | str, locator: str = ""
    ) -> SourceCitation:
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        digest = hashlib.sha256(data).hexdigest()
        return cls(source_id=source_id, hash=digest, locator=locator)


class AgentError(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    message: str
    agent: AgentName


class CostBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0

    def __add__(self, other: CostBreakdown) -> CostBreakdown:
        return CostBreakdown(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            usd=round(self.usd + other.usd, 6),
        )


class WorkerResult(BaseModel):
    """The slot a single worker fills.

    ``data`` is intentionally a free-form dict at this layer so individual
    agents can evolve their output schema without churning the supervisor.
    Each agent's output is validated against its own typed schema before it
    lands here.
    """

    model_config = ConfigDict(frozen=True)

    agent: AgentName
    status: WorkerStatus
    data: dict[str, Any] = Field(default_factory=dict)
    citations: tuple[SourceCitation, ...] = ()
    latency_ms: float = 0.0
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    retry_count: int = 0
    error: AgentError | None = None


def _merge_worker_results(
    existing: dict[AgentName, WorkerResult],
    incoming: dict[AgentName, WorkerResult],
) -> dict[AgentName, WorkerResult]:
    """LangGraph reducer for the worker_results channel.

    Workers may run in parallel branches; each branch returns a single-entry
    dict. The reducer composes them into the supervisor's view of the world.
    Later writes for the same agent overwrite earlier writes (a retry).
    """

    merged = dict(existing)
    merged.update(incoming)
    return merged


class ResearchState(BaseModel):
    """The full run state.

    Mutation discipline: workers return a partial dict; LangGraph merges via
    the reducers below. The state itself is treated as immutable from any
    agent's point of view.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    run_id: str = Field(default_factory=_new_run_id)
    ticker: str
    requested_at: datetime = Field(default_factory=_utcnow)
    requested_by: str = "anonymous"

    worker_results: Annotated[dict[AgentName, WorkerResult], _merge_worker_results] = Field(
        default_factory=dict
    )
    note: dict[str, Any] | None = None
    critique: dict[str, Any] | None = None
    errors: tuple[AgentError, ...] = ()

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, v: str) -> str:
        normalized = v.strip().upper()
        if not normalized or not normalized.replace(".", "").replace("-", "").isalnum():
            raise ValueError(f"invalid ticker: {v!r}")
        if len(normalized) > 10:
            raise ValueError(f"ticker too long: {v!r}")
        return normalized

    def total_cost(self) -> CostBreakdown:
        total = CostBreakdown()
        for result in self.worker_results.values():
            total = total + result.cost
        return total

    def all_citations(self) -> tuple[SourceCitation, ...]:
        return tuple(
            citation for result in self.worker_results.values() for citation in result.citations
        )

    def has_worker(self, name: AgentName) -> bool:
        return name in self.worker_results

    def with_error(self, error: AgentError) -> Self:
        return self.model_copy(update={"errors": (*self.errors, error)})
