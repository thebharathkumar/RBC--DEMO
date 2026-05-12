"""Market data adapter.

Primary: yfinance. Polygon fallback is wired in milestone 4 once the API key
provisioning story is settled.

The adapter is split into a pure ``compute_snapshot`` (deterministic, testable
without network) and a thin ``fetch`` method that calls the upstream and feeds
the computation. Tests inject a ``PriceSeries`` directly.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from src.models.note import MarketSnapshot
from src.models.state import SourceCitation


@dataclass(frozen=True, slots=True)
class PriceSeries:
    """Closing prices for a single instrument, oldest first."""

    ticker: str
    timestamps: tuple[datetime, ...]
    closes: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.timestamps) != len(self.closes):
            raise ValueError("timestamps and closes must align")
        if len(self.closes) < 2:
            raise ValueError("need at least two observations")
        if any(not math.isfinite(c) or c <= 0 for c in self.closes):
            raise ValueError("closes must be positive and finite")

    def last(self) -> float:
        return self.closes[-1]

    def return_pct(self, days: int) -> float | None:
        if len(self.closes) < days + 1:
            return None
        prior = self.closes[-(days + 1)]
        return round((self.closes[-1] / prior - 1.0) * 100.0, 4)

    def realized_vol_pct(self) -> float | None:
        if len(self.closes) < 21:
            return None
        rets = [math.log(self.closes[i] / self.closes[i - 1]) for i in range(1, len(self.closes))]
        if len(rets) < 20:
            return None
        sample = rets[-252:] if len(rets) >= 252 else rets
        stdev = statistics.pstdev(sample)
        annualised = stdev * math.sqrt(252) * 100.0
        return round(annualised, 4)

    def max_drawdown_pct(self) -> float | None:
        if len(self.closes) < 2:
            return None
        peak = self.closes[0]
        worst = 0.0
        for c in self.closes:
            peak = max(peak, c)
            dd = (c / peak) - 1.0
            worst = min(worst, dd)
        return round(worst * 100.0, 4)


def compute_snapshot(
    target: PriceSeries, *, benchmark: PriceSeries | None = None
) -> MarketSnapshot:
    """Pure projection from price history to the note's market block.

    ``benchmark`` is reserved for the beta calculation; this is the seam where
    the SPX series will be plugged in. We leave beta None when no benchmark
    is provided rather than computing a vacuous one.
    """

    beta: float | None = None
    if benchmark is not None and benchmark.ticker != target.ticker:
        beta = _beta_vs(target, benchmark)

    return MarketSnapshot(
        last_price=target.last(),
        return_1m_pct=target.return_pct(21),
        return_3m_pct=target.return_pct(63),
        return_1y_pct=target.return_pct(252),
        realized_vol_pct=target.realized_vol_pct(),
        beta_vs_spx=beta,
        max_drawdown_pct=target.max_drawdown_pct(),
    )


def _beta_vs(target: PriceSeries, benchmark: PriceSeries) -> float | None:
    n = min(len(target.closes), len(benchmark.closes))
    if n < 30:
        return None
    t = target.closes[-n:]
    b = benchmark.closes[-n:]
    target_rets = [math.log(t[i] / t[i - 1]) for i in range(1, n)]
    bench_rets = [math.log(b[i] / b[i - 1]) for i in range(1, n)]
    var_b = statistics.pvariance(bench_rets)
    if var_b == 0:
        return None
    mean_t = statistics.fmean(target_rets)
    mean_b = statistics.fmean(bench_rets)
    cov = statistics.fmean(
        [(tr - mean_t) * (br - mean_b) for tr, br in zip(target_rets, bench_rets, strict=False)]
    )
    return round(cov / var_b, 4)


class PriceFetcher(Protocol):
    def fetch(self, ticker: str, *, days: int) -> PriceSeries: ...


class YFinancePriceFetcher:
    """Live yfinance fetcher. Imported lazily so tests do not pull yfinance."""

    @retry(
        reraise=True,
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=2, max=8),
    )
    def fetch(self, ticker: str, *, days: int = 365) -> PriceSeries:
        import yfinance  # local import keeps test imports cheap

        start = datetime.now(UTC) - timedelta(days=days + 30)
        history = yfinance.Ticker(ticker).history(start=start, auto_adjust=True)
        if history.empty:
            raise RuntimeError(f"no price data for {ticker}")
        timestamps = tuple(ts.to_pydatetime() for ts in history.index.to_pydatetime())
        closes = tuple(float(c) for c in history["Close"].tolist())
        return PriceSeries(ticker=ticker.upper(), timestamps=timestamps, closes=closes)


class MarketDataAdapter:
    """Wraps a ``PriceFetcher`` and exposes the citation-bearing surface."""

    def __init__(self, fetcher: PriceFetcher | None = None) -> None:
        self._fetcher = fetcher or YFinancePriceFetcher()

    def snapshot(self, ticker: str, *, days: int = 365) -> tuple[MarketSnapshot, SourceCitation]:
        series = self._fetcher.fetch(ticker, days=days)
        snapshot = compute_snapshot(series)
        # Cite the deterministic projection of the series: any tampering with
        # the inputs changes the hash, which fails the audit at replay time.
        payload = "|".join(
            f"{ts.isoformat()}:{c}" for ts, c in zip(series.timestamps, series.closes, strict=False)
        )
        citation = SourceCitation.for_payload(
            source_id=f"yfinance:{series.ticker}",
            payload=payload,
            locator=f"window={days}d,n={len(series.closes)}",
        )
        return snapshot, citation
