"""Research supervisor.

At this milestone the supervisor is a planner only; it sets initial defaults
on the state. Branch-and-merge orchestration lives in ``graph/builder.py``.
The supervisor will pick up routing logic (skip workers when upstream data
is unavailable, decide on critique loop revisions) in milestone 5.
"""

from __future__ import annotations

import structlog

from src.models.state import AgentName, ResearchState

_log = structlog.get_logger(__name__)


class ResearchSupervisor:
    name = AgentName.SUPERVISOR

    def plan(self, state: ResearchState) -> dict[str, object]:
        _log.info(
            "supervisor.plan",
            run_id=state.run_id,
            ticker=state.ticker,
        )
        # Today the plan is static: run every available worker in parallel,
        # then synthesise. The plan node remains so the trace records a
        # supervisor step and we can layer real routing into it later.
        return {}
