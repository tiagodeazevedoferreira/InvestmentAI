from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RegimeObservation:
    label: str
    realized_volatility: float | None
    observations: int


REGIME_THRESHOLDS = {
    "low": 0.015,
    "high": 0.030,
}


def classify_regime(
    frame: pd.DataFrame,
    *,
    decision_timestamp=None,
    window: int = 20,
    low_threshold: float = REGIME_THRESHOLDS["low"],
    high_threshold: float = REGIME_THRESHOLDS["high"],
) -> RegimeObservation:
    """Classify volatility using only closes available at the decision bar.

    Realized volatility is the standard deviation of log returns over the
    trailing ``window`` returns. No future bars are inspected. Thresholds are
    deliberately fixed and explicit so the label cannot leak future sample
    information into calibration.
    """
    if window < 2:
        raise ValueError("window must be at least 2")
    if not 0 < low_threshold < high_threshold:
        raise ValueError("thresholds must satisfy 0 < low < high")
    if "Close" not in frame.columns:
        raise ValueError("frame must contain Close")

    closes = pd.to_numeric(frame["Close"], errors="coerce").dropna()
    if decision_timestamp is not None:
        ts = pd.Timestamp(decision_timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        index = pd.DatetimeIndex(closes.index)
        if index.tz is None:
            index = index.tz_localize("UTC")
        else:
            index = index.tz_convert("UTC")
        closes = closes.copy()
        closes.index = index
        closes = closes.loc[closes.index <= ts]

    if len(closes) < window + 1:
        return RegimeObservation("insufficient_history", None, max(0, len(closes) - 1))

    returns = (closes / closes.shift(1)).apply(math.log).dropna()
    trailing = returns.tail(window)
    if len(trailing) < window:
        return RegimeObservation("insufficient_history", None, len(trailing))

    volatility = float(trailing.std(ddof=1))
    if volatility < low_threshold:
        label = "low"
    elif volatility >= high_threshold:
        label = "high"
    else:
        label = "normal"
    return RegimeObservation(label, volatility, len(trailing))
