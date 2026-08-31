import numpy as np
import pandas as pd

FEATURES = ["return_1d", "return_5d", "volatility_20d", "EMA9_gap", "EMA21_gap", "RSI14", "BB_position", "volume_change"]

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    from .technical import indicators
    x = indicators(df)
    close = x["Close"].astype(float)
    x["return_1d"] = close.pct_change()
    x["return_5d"] = close.pct_change(5)
    x["volatility_20d"] = close.pct_change().rolling(20).std()
    x["EMA9_gap"] = close / x["EMA9"] - 1
    x["EMA21_gap"] = close / x["EMA21"] - 1
    x["BB_position"] = (close - x["BB_LOWER"]) / (x["BB_UPPER"] - x["BB_LOWER"])
    x["volume_change"] = x["Volume"].pct_change()
    x["target_5d_up"] = (close.shift(-5) > close).astype(float)
    return x.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURES)

def chronological_split(df, train_ratio=0.7, validation_ratio=0.15):
    if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1 or train_ratio + validation_ratio >= 1:
        raise ValueError("Invalid chronological split ratios")
    n = len(df)
    a, b = int(n * train_ratio), int(n * (train_ratio + validation_ratio))
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]
