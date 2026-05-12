# Observability

## Tracing

Langfuse v4 holds the canonical trace for every run. Each agent invocation is a span with attributes:

- `agent.name`, `agent.version`
- `model.id`, `model.input_tokens`, `model.output_tokens`, `model.usd_cost`
- `state.input_hash`, `state.output_hash`
- `retry.count`, `retry.attempts`
- `latency.ms`
- `error.type`, `error.message` on failure

The `/traces/:run_id` endpoint mirrors the same data to the frontend.

## Metrics

Prometheus is exposed at `/metrics`. Custom series include:

- `agent_invocation_duration_seconds{agent}`
- `agent_invocation_failures_total{agent,error_type}`
- `external_api_latency_seconds{source}`
- `external_api_circuit_state{source}` (0 closed, 1 half-open, 2 open)
- `run_total_cost_usd`
- `run_total_duration_seconds`

## Logs

structlog produces JSON logs with shared context fields: `run_id`, `ticker`, `agent`, `step`. Logs are not the primary observability surface; Langfuse and Prometheus are. Logs exist to root-cause incidents.

## Alerts

Production deployment defines alerts on circuit breaker open events, p95 latency above 180 seconds, and hallucination rate (computed offline from eval replay) above the threshold defined in `docs/evaluation.md`.
