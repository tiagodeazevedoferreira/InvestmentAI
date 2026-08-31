from __future__ import annotations
import numpy as np
import pandas as pd
from .technical import indicators


def build_features(df: pd.DataFrame, horizon: int = 5) -> tuple[pd.DataFrame, pd.Series]:
    if horizon < 1:
        raise ValueError("horizon must be positive")
    x = indicators(df.copy()).copy()
    close = x["Close"].astype(float)
    x["return_1d"] = close.pct_change()
    x["return_5d"] = close.pct_change(5)
    x["volatility_20d"] = x["return_1d"].rolling(20).std()
    x["volume_change"] = x["Volume"].pct_change()
    x["future_return_5d"] = close.shift(-horizon) / close - 1.0
    y = (x["future_return_5d"] > 0).astype(int)
    feature_cols = ["EMA9", "EMA21", "RSI14", "BB_MIDDLE", "BB_UPPER", "BB_LOWER", "return_1d", "return_5d", "volatility_20d", "volume_change"]
    valid = x[feature_cols + ["future_return_5d"]].replace([np.inf, -np.inf], np.nan).dropna()
    return valid[feature_cols], y.loc[valid.index]


def chronological_split(X: pd.DataFrame, y: pd.Series, train_fraction: float = .7, validation_fraction: float = .15):
    if not 0 < train_fraction < 1 or not 0 <= validation_fraction < 1 or train_fraction + validation_fraction >= 1:
        raise ValueError("invalid chronological split fractions")
    n = len(X)
    a, b = int(n * train_fraction), int(n * (train_fraction + validation_fraction))
    return (X.iloc[:a], y.iloc[:a]), (X.iloc[a:b], y.iloc[a:b]), (X.iloc[b:], y.iloc[b:])
