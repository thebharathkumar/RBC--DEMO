# Data sources

| Source | Adapter | Purpose | Auth | Rate posture |
|---|---|---|---|---|
| SEC EDGAR | `data/edgar.py` | 10-K, 10-Q, 8-K filings | Identifying UA string | 10 req/s, EDGAR fair-use |
| Earnings transcripts | `data/transcripts.py` | Prepared remarks and Q&A | Provider key | Provider-defined |
| yfinance | `data/market.py` | OHLCV, fundamentals | None | Polite caching |
| Polygon | `data/market.py` (fallback) | OHLCV, options | API key | Plan-defined |
| Tavily | `data/news.py` | News with summaries | API key | 1k/mo on free |
| NewsAPI | `data/news.py` (fallback) | News articles | API key | 100/day on free |

## Caching and freshness

All adapters cache by `(source, ticker, window, request_hash)` in Redis with TTLs tuned per source. Filings are stable so TTL is 24 hours; news is volatile so TTL is 15 minutes.

## Failure handling

Every adapter call goes through tenacity with exponential backoff plus jitter and a circuit breaker that opens after five consecutive failures and half-opens after sixty seconds. When both primary and fallback are open, the worker reports `unavailable` and the supervisor records the gap.

## Licensing notes

Free-tier endpoints are used here for portfolio purposes. A production deployment would route through licensed vendor feeds.
