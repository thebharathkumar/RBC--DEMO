# ADR 0002: Call the Anthropic SDK directly, no abstraction layer

## Status

Accepted, 2026-05-12.

## Context

LangChain provides a thin wrapper around the Anthropic SDK. The wrapper is convenient for swapping providers but introduces an extra serialization layer, leaks abstractions, and obscures cost and token telemetry.

## Decision

Use the Anthropic SDK directly for all model calls. LangChain is admitted only where LangGraph requires it for tool calling primitives.

## Rationale

We need fine control over caching headers, tool call schemas, streaming, and token-level cost accounting. Direct SDK calls preserve that control. The added cost of vendor lock-in is acceptable for a single-provider portfolio project.

## Consequences

Switching providers is a focused rewrite of the synthesis and critique entry points, not a config change. We accept that trade-off.
