"""LangGraph wiring.

Topology at this milestone:

    START -> supervisor -> market_data -> synthesizer -> END

Additional worker nodes will fan out in parallel from the supervisor in
milestone 4. We keep the wiring central so all framework knowledge stays in
this module; the agents themselves remain framework-agnostic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from src.agents.market_data import MarketDataAnalyst
from src.agents.supervisor import ResearchSupervisor
from src.agents.synthesizer import Synthesizer
from src.models.state import ResearchState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def build_graph(
    *,
    supervisor: ResearchSupervisor | None = None,
    market_data: MarketDataAnalyst | None = None,
    synthesizer: Synthesizer | None = None,
) -> CompiledStateGraph:
    supervisor = supervisor or ResearchSupervisor()
    market_data = market_data or MarketDataAnalyst()
    synthesizer = synthesizer or Synthesizer()

    def _supervisor_node(state: ResearchState) -> dict[str, object]:
        return supervisor.plan(state)

    def _market_data_node(state: ResearchState) -> dict[str, object]:
        return {"worker_results": market_data.run(state)}

    def _synthesizer_node(state: ResearchState) -> dict[str, object]:
        return synthesizer.run(state)

    graph: StateGraph = StateGraph(ResearchState)
    graph.add_node("supervisor", _supervisor_node)
    graph.add_node("market_data", _market_data_node)
    graph.add_node("synthesizer", _synthesizer_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "market_data")
    graph.add_edge("market_data", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


def run_pipeline(
    ticker: str,
    *,
    requested_by: str = "anonymous",
    supervisor: ResearchSupervisor | None = None,
    market_data: MarketDataAnalyst | None = None,
    synthesizer: Synthesizer | None = None,
) -> ResearchState:
    """Execute the full pipeline synchronously and return the terminal state."""

    compiled = build_graph(supervisor=supervisor, market_data=market_data, synthesizer=synthesizer)
    initial = ResearchState(ticker=ticker, requested_by=requested_by)
    final = compiled.invoke(initial)
    # LangGraph returns either a Pydantic model or a dict depending on
    # version; coerce defensively.
    if isinstance(final, ResearchState):
        return final
    return ResearchState.model_validate(final)
