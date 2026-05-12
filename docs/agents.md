# Agent contracts

Every agent is a pure function over `ResearchState`. Agents must not perform I/O; data adapters do that. Agents call models to reason over data the adapters fetched.

## ResearchSupervisor

Inputs: ticker, run config.
Outputs: a typed plan and a sequence of dispatch decisions.
Failure mode: surfaces unrecoverable errors to the API edge with the partial state.

## FilingsAnalyst

Inputs: ticker, retrieved filings chunks from pgvector.
Outputs: MD&A deltas year over year, segment performance summary, risk factor evolution. Every output carries citations of the form `{accession, page, chunk_hash}`.

## EarningsCallAnalyst

Inputs: last four earnings call transcripts (prepared remarks and Q&A separated).
Outputs: tone delta score, guidance change vector, analyst question hostility distribution, management specificity score.

## MarketDataAnalyst

Inputs: OHLCV and reference data for ticker, sector ETF, SPX.
Outputs: returns table across windows, realized volatility, beta, max drawdown, volume profile, unusual options flag when data is available.

## NewsAndSentimentAnalyst

Inputs: last 60 days of news after MinHash deduplication.
Outputs: theme clusters with sentiment, catalyst classification (priced-in vs pending), source list.

## ComparablesAnalyst

Inputs: peer set fetched by sector and market cap proximity.
Outputs: peer table with EV/EBITDA, EV/Sales, P/E forward, P/B, and percentile rank of target.

## CritiqueAgent

Inputs: draft synthesized note plus all worker outputs.
Outputs: structured critique with severity-tagged findings. Blocking findings force a synthesizer rerun.

## Synthesizer

Inputs: all worker outputs and, on rerun, the previous critique.
Outputs: structured note matching the schema in `docs/architecture.md`. Reruns up to twice.

## Contracts in code

Each agent's input and output models live in `apps/api/src/models/` and are versioned by file. Backward-incompatible changes require a new model version, not an edit in place.
