from __future__ import annotations

import numpy as np
import pandas as pd

from .technical import indicators


def build_features(df: pd.DataFrame, horizon: int = 5) -> tuple[pd.DataFrame, pd.Series]:
    if horizon < 1:
        raise ValueError("horizon must be positive")
    x = indicators(df.copy()).copy()
    close = x["Close"].astype(float)
    ema9 = x["EMA9"].astype(float)
    ema21 = x["EMA21"].astype(float)
    bb_middle = x["BB_MIDDLE"].astype(float)
    bb_upper = x["BB_UPPER"].astype(float)
    bb_lower = x["BB_LOWER"].astype(float)

    x["return_1d"] = close.pct_change()
    x["return_5d"] = close.pct_change(5)
    x["volatility_20d"] = x["return_1d"].rolling(20).std()
    x["volume_change"] = x["Volume"].pct_change()

    # Prefer scale-invariant technical features. Raw price-level indicators
    # (EMA/BB values) drift with the asset price and make the model learn
    # non-stationary level information instead of relative market structure.
    x["ema9_gap"] = ema9 / close - 1.0
    x["ema21_gap"] = ema21 / close - 1.0
    x["ema_spread"] = ema9 / ema21 - 1.0
    x["rsi_centered"] = (x["RSI14"].astype(float) - 50.0) / 50.0
    bb_range = (bb_upper - bb_lower).replace(0.0, np.nan)
    x["bb_position"] = (close - bb_lower) / bb_range
    x["bb_width"] = bb_range / bb_middle.replace(0.0, np.nan)

    x["future_return_5d"] = close.shift(-horizon) / close - 1.0
    y = (x["future_return_5d"] > 0).astype(int)
    feature_cols = [
        "ema9_gap",
        "ema21_gap",
        "ema_spread",
        "rsi_centered",
        "bb_position",
        "bb_width",
        "return_1d",
        "return_5d",
        "volatility_20d",
        "volume_change",
    ]
    valid = x[feature_cols + ["future_return_5d"]].replace([np.inf, -np.inf], np.nan).dropna()
    return valid[feature_cols], y.loc[valid.index]


def chronological_split(X: pd.DataFrame, y: pd.Series, train_fraction: float = .7, validation_fraction: float = .15):
    if not 0 < train_fraction < 1 or not 0 <= validation_fraction < 1 or train_fraction + validation_fraction >= 1:
        raise ValueError("invalid chronological split fractions")
    n = len(X)
    a, b = int(n * train_fraction), int(n * (train_fraction + validation_fraction))
    return (X.iloc[:a], y.iloc[:a]), (X.iloc[a:b], y.iloc[a:b]), (X.iloc[b:], y.iloc[b:])
