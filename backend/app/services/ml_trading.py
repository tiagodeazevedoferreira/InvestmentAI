from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_features


@dataclass(frozen=True)
class MLPredictionRun:
    predictions: pd.Series
    probabilities: pd.Series
    test_rows: int
    folds: int


def purged_walk_forward_predictions(
    df: pd.DataFrame,
    *,
    horizon: int = 5,
    train_size: int = 500,
    test_size: int = 100,
    step: int = 100,
) -> MLPredictionRun:
    """Generate strictly out-of-sample predictions using the same WFV protocol.

    Each model is fitted only on its chronological training window. A purge equal
    to ``horizon`` separates training labels from the test window. Predictions are
    therefore safe to convert into trading signals without look-ahead leakage.
    """
    if min(horizon, train_size, test_size, step) < 1:
        raise ValueError("horizon, train_size, test_size and step must be positive")

    X, y = build_features(df, horizon=horizon)
    if len(X) < train_size + horizon + test_size:
        raise ValueError("insufficient observations for walk-forward predictions")

    predictions: list[pd.Series] = []
    probabilities: list[pd.Series] = []
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

        model = Pipeline([
            ("scale", StandardScaler()),
            ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ])
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
    """Map class 1 to long and class 0 to flat, using only predicted information."""
    pred = predictions.astype(int)
    if not pred.isin([0, 1]).all():
        raise ValueError("predictions must contain only 0 or 1")
    return pred.map({0: -1, 1: 1}).astype(int).rename("signal")
