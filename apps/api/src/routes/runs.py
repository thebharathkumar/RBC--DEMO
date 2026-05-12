"""HTTP control plane for research runs.

The registry is in-memory only at this milestone. A Postgres-backed registry
with the LangGraph checkpointer lands in milestone 5; routing through it then
is a single dependency swap.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from src.graph.builder import run_pipeline
from src.models.state import ResearchState

_log = structlog.get_logger(__name__)

router = APIRouter(prefix="/runs", tags=["runs"])


class _Registry:
    """Process-local store of terminal run states. Thread-safe by design."""

    def __init__(self) -> None:
        self._states: dict[str, ResearchState] = {}
        self._lock = threading.RLock()

    def put(self, state: ResearchState) -> None:
        with self._lock:
            self._states[state.run_id] = state

    def get(self, run_id: str) -> ResearchState | None:
        with self._lock:
            return self._states.get(run_id)

    def list_recent(self, limit: int = 20) -> list[ResearchState]:
        with self._lock:
            return list(self._states.values())[-limit:]


_registry = _Registry()


def get_registry() -> _Registry:
    return _registry


class RunRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    requested_by: str = "anonymous"


class RunSummary(BaseModel):
    run_id: str
    ticker: str
    note_available: bool
    total_cost_usd: float
    worker_count: int


def _summarise(state: ResearchState) -> RunSummary:
    return RunSummary(
        run_id=state.run_id,
        ticker=state.ticker,
        note_available=state.note is not None,
        total_cost_usd=state.total_cost().usd,
        worker_count=len(state.worker_results),
    )


@router.post("", response_model=RunSummary, status_code=201)
async def create_run(request: RunRequest) -> RunSummary:
    _log.info("runs.create", ticker=request.ticker)
    state = await asyncio.to_thread(run_pipeline, request.ticker, requested_by=request.requested_by)
    _registry.put(state)
    return _summarise(state)


@router.get("/{run_id}", response_model=ResearchState)
async def get_run(
    run_id: Annotated[str, Path(min_length=8, max_length=64)],
) -> ResearchState:
    state = _registry.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return state


@router.get("", response_model=list[RunSummary])
async def list_runs(limit: int = 20) -> list[RunSummary]:
    return [_summarise(s) for s in _registry.list_recent(limit=limit)]
