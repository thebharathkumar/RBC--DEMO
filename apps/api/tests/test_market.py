"""Tests for the deterministic price-to-snapshot projection."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from src.data.market import PriceSeries, compute_snapshot


def _series(closes: list[float], ticker: str = "AAPL") -> PriceSeries:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    timestamps = tuple(start + timedelta(days=i) for i in range(len(closes)))
    return PriceSeries(ticker=ticker, timestamps=timestamps, closes=tuple(closes))


def test_return_pct_uses_window_length() -> None:
    series = _series([100.0] * 22 + [110.0])
    assert series.return_pct(22) == pytest.approx(10.0)


def test_return_pct_short_history_returns_none() -> None:
    series = _series([100.0, 101.0])
    assert series.return_pct(21) is None


def test_realized_vol_is_annualised() -> None:
    # 30 days of alternating +/-1% logs -> stdev approx 1%; annualised approx
    # 1% * sqrt(252) approx 15.87%.
    closes = [100.0]
    for i in range(30):
        closes.append(closes[-1] * (1.01 if i % 2 == 0 else 1 / 1.01))
    series = _series(closes)
    vol = series.realized_vol_pct()
    assert vol is not None
    assert 10.0 < vol < 25.0


def test_max_drawdown_captures_peak_to_trough() -> None:
    series = _series([100.0, 120.0, 110.0, 90.0, 95.0])
    dd = series.max_drawdown_pct()
    assert dd == pytest.approx(-25.0)


def test_compute_snapshot_populates_fields() -> None:
    closes = [100.0 + i * 0.1 for i in range(300)]
    series = _series(closes)
    snapshot = compute_snapshot(series)
    assert snapshot.last_price == pytest.approx(closes[-1])
    assert snapshot.return_1m_pct is not None
    assert snapshot.return_3m_pct is not None
    assert snapshot.return_1y_pct is not None
    assert snapshot.max_drawdown_pct is not None


def test_price_series_rejects_non_positive_closes() -> None:
    with pytest.raises(ValueError):
        _series([100.0, 0.0])


def test_price_series_rejects_non_finite() -> None:
    with pytest.raises(ValueError):
        _series([100.0, math.inf])
