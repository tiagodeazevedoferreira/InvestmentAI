from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from .data_quality import MarketDataQualityReport, validate_market_data
from .openbb_market_data import OpenBBMarketDataProvider


MarketDataSource = Literal["fixture", "provider"]
CI_SYMBOLS = ("PETR4", "VALE3", "ITUB4")
CI_FIXTURE_START = "2021-01-04"
CI_FIXTURE_ROWS = 1500


# The CI fixture is intentionally synthetic. It is not presented as market
# history and must never be used as evidence about real asset performance.
# Its purpose is to make deterministic algorithmic validation independent of
# third-party provider availability, rate limits, and network conditions.
_FIXTURE_SEEDS = {"PETR4": 11, "VALE3": 23, "ITUB4": 37}
_FIXTURE_BASE_PRICES = {"PETR4": 24.0, "VALE3": 68.0, "ITUB4": 31.0}


def _fixture_history(symbol: str) -> pd.DataFrame:
    normalized = symbol.strip().upper()
    if normalized not in CI_SYMBOLS:
        raise ValueError(f"unsupported CI fixture symbol: {symbol}")

    rng = np.random.default_rng(_FIXTURE_SEEDS[normalized])
    index = pd.date_range(CI_FIXTURE_START, periods=CI_FIXTURE_ROWS, freq="B", tz="UTC", name="date")
    n = len(index)
    t = np.arange(n, dtype=float)

    # Multiple deterministic regimes keep the classification target varied
    # while avoiding any dependency on external market data.
    regime = np.where((t // 180) % 2 == 0, 1.0, -1.0)
    cycle = 0.0018 * np.sin(2.0 * np.pi * t / 55.0)
    medium_cycle = 0.0012 * np.sin(2.0 * np.pi * t / 210.0 + 0.7)
    noise = rng.normal(0.0, 0.006, n)
    returns = 0.00025 * regime + cycle + medium_cycle + noise
    returns = np.clip(returns, -0.035, 0.035)

    close = np.empty(n, dtype=float)
    close[0] = _FIXTURE_BASE_PRICES[normalized]
    close[1:] = close[0] * np.cumprod(1.0 + returns[1:])

    overnight = rng.normal(0.0, 0.0025, n)
    open_price = close / (1.0 + np.clip(returns, -0.08, 0.08))
    open_price *= 1.0 + overnight

    intraday_range = np.clip(0.004 + np.abs(rng.normal(0.0, 0.003, n)), 0.004, 0.025)
    high = np.maximum(open_price, close) * (1.0 + intraday_range)
    low = np.minimum(open_price, close) * (1.0 - intraday_range)

    volume_base = {"PETR4": 1.2e8, "VALE3": 9.0e7, "ITUB4": 7.5e7}[normalized]
    volume = volume_base * np.exp(rng.normal(0.0, 0.18, n))

    frame = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )
    return frame


def load_market_history(
    symbol: str,
    *,
    source: MarketDataSource = "fixture",
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
) -> tuple[pd.DataFrame, MarketDataQualityReport | None]:
    """Load deterministic CI data or explicitly requested provider data."""
    if source not in ("fixture", "provider"):
        raise ValueError("source must be 'fixture' or 'provider'")

    if source == "provider":
        provider = OpenBBMarketDataProvider()
        frame, quality = provider.historical_with_quality(
            symbol,
            start=start,
            end=end,
            interval=interval,
        )
        return frame, quality

    frame = _fixture_history(symbol)
    if start is not None:
        frame = frame.loc[pd.Timestamp(start, tz="UTC") :]
    if end is not None:
        frame = frame.loc[: pd.Timestamp(end, tz="UTC")]
    if frame.empty:
        raise ValueError(f"CI fixture has no rows for {symbol} in requested range")

    quality = validate_market_data(symbol, frame, interval=interval)
    if not quality.valid:
        raise ValueError(f"CI fixture quality gate failed: {quality}")
    return frame, quality


__all__ = ["CI_SYMBOLS", "MarketDataSource", "load_market_history"]
