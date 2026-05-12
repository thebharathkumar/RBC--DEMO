# ADR 0001: Use LangGraph for supervisor-worker orchestration

## Status

Accepted, 2026-05-12.

## Context

The platform needs a runtime that supports parallel worker fan-out, conditional edges, retries, human-in-the-loop pause points, and full replay from a checkpoint. We evaluated three options.

1. Hand-rolled async task graph in plain Python.
2. Temporal.
3. LangGraph.

## Decision

Adopt LangGraph.

## Rationale

A hand-rolled graph is the simplest thing that works, but reimplementing checkpoint, replay, and human-in-the-loop primitives is non-trivial and would be the bulk of the build.

Temporal is the strongest choice for a production multi-team system. It is overkill for a single-tenant research workflow with sub-three-minute runs and would add an operational surface (Temporal cluster) that is not justified at this scale.

LangGraph gives us typed state, conditional edges, parallel branches, a checkpointer abstraction with a Postgres backend, and explicit interrupt points for human review. It is closer to the agent runtime semantics we want than a general workflow engine.

## Consequences

We accept a tighter coupling to the LangGraph API. The agent contracts in `docs/agents.md` are designed so the agent functions themselves are framework-agnostic; only the supervisor in `graph/builder.py` knows about LangGraph specifically. A migration to Temporal or a hand-rolled runner would be a rewrite of the supervisor, not the agents.
