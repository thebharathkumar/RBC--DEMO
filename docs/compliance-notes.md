# Compliance notes

This is a portfolio prototype, not a regulated production system. The notes below describe the safety posture baked in here and the gaps a real bank deployment would close.

## What is implemented

1. Every generated note includes a disclaimer stating that it is automated research support, not investment advice.
2. Every numeric or quoted claim in the output carries an inline citation that resolves to a source registry entry with a content hash.
3. A full audit log records the input ticker, requesting user, model identifiers and versions, source hashes retrieved, and final output hash. Stored in Postgres.
4. A prompt injection middleware scans retrieved content (filings text, news, transcripts) before that content is included in any LLM context.
5. No PII, MNPI, or proprietary RBC data is ingested. The platform only touches public filings, public market data, and public news.

## What a production deployment would add

1. Identity and entitlement enforcement through the firm IDP and an authorization service that scopes access by desk and instrument universe.
2. Source ingestion through licensed vendor feeds rather than free-tier public APIs.
3. A model gateway with DLP, logging, and model risk management sign-off.
4. A research compliance review queue gating any analyst-facing publication.
5. Retention and legal hold policies on the audit log aligned with the firm's records management policy.
6. WORM storage for final published notes.

## Data handling

No data is sent to third parties beyond the explicitly configured upstreams (Anthropic, Langfuse, the chosen news provider). Outbound traffic is documented in `docs/data-sources.md`. The deployment region pin is in `infra/render.yaml`.
