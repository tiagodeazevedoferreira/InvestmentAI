from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_features
from .market_replay import MarketBar


@dataclass(frozen=True)
class MLPredictionRun:
    predictions: pd.Series
    probabilities: pd.Series
    test_rows: int
    folds: int


def purged_walk_forward_predictions(df: pd.DataFrame, *, horizon: int = 5, train_size: int = 500, test_size: int = 100, step: int = 100) -> MLPredictionRun:
    if min(horizon, train_size, test_size, step) < 1:
        raise ValueError("horizon, train_size, test_size and step must be positive")
    X, y = build_features(df, horizon=horizon)
    if len(X) < train_size + horizon + test_size:
        raise ValueError("insufficient observations for walk-forward predictions")
    predictions, probabilities = [], []
    start = 0
    folds = 0
    while start + train_size + horizon + test_size <= len(X):
        train_end = start + train_size
        test_start = train_end + horizon
        test_end = test_start + test_size
        X_train, y_train = X.iloc[start:train_end], y.iloc[start:train_end]
        X_test = X.iloc[test_start:test_end]
        if y_train.nunique() < 2:
            start += step
            continue
        model = Pipeline([("scale", StandardScaler()), ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))])
        model.fit(X_train, y_train)
        predictions.append(pd.Series(model.predict(X_test), index=X_test.index, name="prediction"))
        probabilities.append(pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index, name="probability"))
        folds += 1
        start += step
    if not predictions:
        raise ValueError("no valid walk-forward prediction folds were produced")
    pred = pd.concat(predictions).sort_index()
    prob = pd.concat(probabilities).sort_index()
    if pred.index.has_duplicates:
        raise ValueError("walk-forward prediction windows overlap")
    if not np.isfinite(prob.to_numpy()).all():
        raise ValueError("non-finite model probabilities")
    return MLPredictionRun(predictions=pred, probabilities=prob, test_rows=len(pred), folds=folds)


def predictions_to_long_only_signals(predictions: pd.Series) -> pd.Series:
    pred = predictions.astype(int)
    if not pred.isin([0, 1]).all():
        raise ValueError("predictions must contain only 0 or 1")
    return pred.map({0: -1, 1: 1}).astype(int).rename("signal")


def probabilities_to_signals(
    probabilities: pd.Series,
    *,
    threshold: float = 0.60,
) -> pd.Series:
    """Convert timestamped model probabilities into deterministic long-only signals."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    if not isinstance(probabilities, pd.Series):
        raise ValueError("probabilities must be a pandas Series")

    if not probabilities.index.is_unique:
        raise ValueError("probabilities index must be unique")

    if not probabilities.index.is_monotonic_increasing:
        raise ValueError("probabilities index must be chronological")

    values = pd.to_numeric(probabilities, errors="coerce").to_numpy(dtype=float)

    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("probabilities must be finite values in [0, 1]")

    return pd.Series(
        np.where(values >= threshold, 1, -1).astype(int),
        index=probabilities.index,
        name="signal",
    )


def signals_to_backtest_function(signals: pd.Series):
    """Adapt timestamped signals to the Backtester signal callback contract."""
    if not isinstance(signals, pd.Series):
        raise ValueError("signals must be a pandas Series")

    if not isinstance(signals.index, pd.DatetimeIndex):
        raise ValueError("signals index must be a DatetimeIndex")

    if not signals.index.is_unique:
        raise ValueError("signals index must be unique")

    if not signals.index.is_monotonic_increasing:
        raise ValueError("signals index must be chronological")

    values = pd.to_numeric(signals, errors="coerce")

    if values.isna().any() or not values.isin([-1, 0, 1]).all():
        raise ValueError("signals must contain only -1, 0, or 1")

    normalized = values.astype(int).copy()
    if normalized.index.tz is None:
        normalized.index = normalized.index.tz_localize("UTC")
    else:
        normalized.index = normalized.index.tz_convert("UTC")

    signal_map = normalized.to_dict()

    def signal_fn(bar: MarketBar) -> int:
        timestamp = pd.Timestamp(bar.timestamp)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        return int(signal_map.get(timestamp, 0))

    return signal_fn
