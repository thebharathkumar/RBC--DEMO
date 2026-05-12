# Architecture

This document is the authoritative description of the runtime topology. ADRs in `docs/adr/` capture the rationale for individual decisions.

## Goals

1. Auditable: every claim in the final note is traceable to a retrieved source artifact identified by a content hash.
2. Observable: every agent invocation is traced in Langfuse with cost, latency, retry, and error attributes.
3. Resilient: every external dependency is wrapped in a retry policy and a circuit breaker.
4. Reproducible: a run is fully replayable from any checkpoint via the LangGraph checkpointer.
5. Cheap to fail: the supervisor short-circuits when a worker's data is unavailable rather than fabricating.

## Component map

The platform splits into five tiers.

1. Edge: FastAPI, SSE for live trace streaming, REST for control plane.
2. Orchestration: LangGraph supervisor and worker subgraphs, checkpointed to Postgres.
3. Data adapters: EDGAR, transcripts, market data, news. Each adapter owns its own retry policy and circuit breaker.
4. Synthesis: Anthropic SDK direct calls. Sonnet for synthesis and critique, Haiku for extraction.
5. Storage: Postgres for state, pgvector for filing chunks, Redis for cache and rate limit.

## State shape

`ResearchState` is a Pydantic v2 model. It flows through every node and is the only object the supervisor mutates. Workers receive a read-only view of the state plus a typed slot they are allowed to fill.

## Failure model

A worker reports one of `ok`, `partial`, `unavailable`, or `error`. The supervisor's plan node decides whether to proceed, retry, or mark the section as unavailable in the final note. The note never silently drops a section; it explicitly states what could not be sourced.

## Streaming

Each node emits a `NodeEvent` to a per-run Redis pubsub channel. The SSE endpoint multiplexes that channel to the frontend.

## Out of scope for milestone 1

Implementation of the supervisor, workers, and adapters is delivered in milestones 2 through 6.
