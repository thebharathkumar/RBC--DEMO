# Evaluation methodology

## Why

Evals are the only honest signal that a multi-agent system works. Smoke tests prove the wiring; evals prove the output.

## Pinned ticker set

Twelve tickers were chosen to span sector, market cap, and disclosure complexity. The selection is frozen until eval v2.

| Ticker | Sector | Notes |
|---|---|---|
| AAPL | Information technology | Mega cap, deep coverage |
| MSFT | Information technology | Cloud transition |
| JPM | Financials | Money center bank |
| GS | Financials | Investment bank |
| XOM | Energy | Integrated oil |
| NEE | Utilities | Regulated plus renewables |
| UNH | Health care | Managed care |
| LLY | Health care | Pharma, GLP-1 cycle |
| KO | Consumer staples | Defensive |
| HD | Consumer discretionary | Housing cyclical |
| LMT | Industrials | Defense |
| TSLA | Consumer discretionary | High-narrative |

## Gold standards

Each ticker has a hand-authored reference note covering: a one-paragraph thesis, three risks, three recent catalysts, and twenty yes/no factual questions. The reference is stored in `apps/api/src/evals/fixtures/`.

## Metrics

- Citation completeness: fraction of numeric or quoted claims with a valid source citation.
- Factual accuracy: pass rate on the twenty yes/no questions.
- Risk recall: fraction of gold-standard risks surfaced in the generated note.
- Hallucination rate: claims unsupported by any retrieved source.
- Latency: p50 and p95 per agent and end-to-end.
- Cost: USD per run.

## Thresholds

CI fails the eval job on regression beyond:

- Citation completeness drop greater than 2 percentage points.
- Factual accuracy drop greater than 3 percentage points.
- Hallucination rate increase greater than 1 percentage point.
- p95 end-to-end latency increase greater than 20 percent.

## Replay

Failed eval runs are replayable from the LangGraph checkpointer to support root-causing.
