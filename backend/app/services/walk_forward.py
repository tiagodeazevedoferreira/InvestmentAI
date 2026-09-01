from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_features


@dataclass(frozen=True)
class WalkForwardFold:
    fold: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    baseline_balanced_accuracy: float
    baseline_macro_f1: float
    model_balanced_accuracy: float
    model_macro_f1: float
    test_rows: int


@dataclass(frozen=True)
class WalkForwardResult:
    symbol: str
    folds: tuple[WalkForwardFold, ...]
    model_balanced_accuracy: float
    model_macro_f1: float
    baseline_balanced_accuracy: float
    baseline_macro_f1: float


def _baseline_predictions(X: pd.DataFrame) -> np.ndarray:
    """EMA crossover baseline using the scale-invariant feature representation.

    The previous implementation compared raw EMA price levels.  The feature
    stability intervention intentionally removes those raw levels, so the
    equivalent crossover is ema9_gap > ema21_gap.
    """
    required = {"ema9_gap", "ema21_gap"}
    missing = required.difference(X.columns)
    if missing:
        raise ValueError(f"baseline features missing: {sorted(missing)}")
    return (X["ema9_gap"] > X["ema21_gap"]).astype(int).to_numpy()


def purged_walk_forward(
    df: pd.DataFrame,
    symbol: str,
    *,
    horizon: int = 5,
    train_size: int = 500,
    test_size: int = 100,
    step: int = 100,
) -> WalkForwardResult:
    if min(horizon, train_size, test_size, step) < 1:
        raise ValueError("horizon, train_size, test_size and step must be positive")

    X, y = build_features(df, horizon=horizon)
    if len(X) < train_size + horizon + test_size:
        raise ValueError("insufficient observations for walk-forward validation")

    folds: list[WalkForwardFold] = []
    start = 0
    fold = 1
    while start + train_size + horizon + test_size <= len(X):
        train_end = start + train_size
        test_start = train_end + horizon  # purge overlapping future labels
        test_end = test_start + test_size

        X_train, y_train = X.iloc[start:train_end], y.iloc[start:train_end]
        X_test, y_test = X.iloc[test_start:test_end], y.iloc[test_start:test_end]

        if y_train.nunique() < 2 or y_test.nunique() < 2:
            start += step
            fold += 1
            continue

        model = Pipeline([
            ("scale", StandardScaler()),
            ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ])
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        baseline = _baseline_predictions(X_test)

        folds.append(WalkForwardFold(
            fold=fold,
            train_start=str(X_train.index[0]),
            train_end=str(X_train.index[-1]),
            test_start=str(X_test.index[0]),
            test_end=str(X_test.index[-1]),
            baseline_balanced_accuracy=float(balanced_accuracy_score(y_test, baseline)),
            baseline_macro_f1=float(f1_score(y_test, baseline, average="macro")),
            model_balanced_accuracy=float(balanced_accuracy_score(y_test, pred)),
            model_macro_f1=float(f1_score(y_test, pred, average="macro")),
            test_rows=len(X_test),
        ))
        start += step
        fold += 1

    if not folds:
        raise ValueError("no valid walk-forward folds were produced")

    return WalkForwardResult(
        symbol=symbol,
        folds=tuple(folds),
        model_balanced_accuracy=float(np.mean([f.model_balanced_accuracy for f in folds])),
        model_macro_f1=float(np.mean([f.model_macro_f1 for f in folds])),
        baseline_balanced_accuracy=float(np.mean([f.baseline_balanced_accuracy for f in folds])),
        baseline_macro_f1=float(np.mean([f.baseline_macro_f1 for f in folds])),
    )
