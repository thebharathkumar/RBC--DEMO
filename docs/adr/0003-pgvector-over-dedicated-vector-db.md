# ADR 0003: pgvector over a dedicated vector database

## Status

Accepted, 2026-05-12.

## Context

The platform needs vector retrieval over filings chunks. Options considered: pgvector, Pinecone, Weaviate, Qdrant.

## Decision

Use pgvector in the same Postgres instance that holds operational state and the audit log.

## Rationale

Filings corpora are small relative to web-scale retrieval workloads. The largest 10-K is on the order of 1 to 2 MB of text, chunked to a few thousand vectors. A single Postgres instance comfortably holds the working set for a multi-hundred-ticker watchlist.

Co-locating embeddings with the relational state means we can join citation hashes to filing metadata in one query and we keep operational complexity to a single managed datastore.

## Consequences

If retrieval latency degrades past a defined SLO we revisit. The retrieval interface in `data/vectorstore.py` is small enough that swapping to a dedicated store is bounded work.
