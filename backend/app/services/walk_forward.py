from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, f1_score, log_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_features


@dataclass(frozen=True)
class RegimeMetrics:
    regime: str
    test_rows: int
    raw_brier: float
    calibrated_brier: float
    selected_brier: float
    raw_ece: float
    calibrated_ece: float
    selected_ece: float
    selected_source: str


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
    raw_brier: float
    calibrated_brier: float
    raw_log_loss: float
    calibrated_log_loss: float
    raw_ece: float
    calibrated_ece: float
    regime_metrics: tuple[RegimeMetrics, ...]
    test_rows: int


@dataclass(frozen=True)
class WalkForwardResult:
    symbol: str
    folds: tuple[WalkForwardFold, ...]
    model_balanced_accuracy: float
    model_macro_f1: float
    baseline_balanced_accuracy: float
    baseline_macro_f1: float
    raw_brier: float
    calibrated_brier: float
    raw_log_loss: float
    calibrated_log_loss: float
    raw_ece: float
    calibrated_ece: float


def _baseline_predictions(X: pd.DataFrame) -> np.ndarray:
    """EMA crossover baseline using the scale-invariant feature representation."""
    required = {"ema9_gap", "ema21_gap"}
    missing = required.difference(X.columns)
    if missing:
        raise ValueError(f"baseline features missing: {sorted(missing)}")
    return (X["ema9_gap"] > X["ema21_gap"]).astype(int).to_numpy()


def _expected_calibration_error(y_true: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    """Return equal-width expected calibration error without fitting on labels."""
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(y)
    if total == 0:
        return float("nan")

    ece = 0.0
    for i in range(bins):
        if i == bins - 1:
            mask = (p >= edges[i]) & (p <= edges[i + 1])
        else:
            mask = (p >= edges[i]) & (p < edges[i + 1])
        if not np.any(mask):
            continue
        ece += (np.sum(mask) / total) * abs(float(np.mean(p[mask])) - float(np.mean(y[mask])))
    return float(ece)


def _calibrated_model(train_rows: int) -> CalibratedClassifierCV:
    """Build a causal Platt calibrator using ordered CV inside each train fold."""
    if train_rows < 6:
        raise ValueError("at least 6 training rows are required for probability calibration")
    n_splits = min(5, train_rows - 1)
    base_model = Pipeline([
        ("scale", StandardScaler()),
        ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    return CalibratedClassifierCV(
        estimator=base_model,
        method="sigmoid",
        cv=TimeSeriesSplit(n_splits=n_splits),
    )


def _volatility_regime(X_train: pd.DataFrame, X_test: pd.DataFrame) -> pd.Series:
    """Classify test rows using a threshold learned only from the training window."""
    threshold = float(X_train["volatility_20d"].median())
    return pd.Series(
        np.where(X_test["volatility_20d"].to_numpy() <= threshold, "low_vol", "high_vol"),
        index=X_test.index,
        name="regime",
    )


def _selected_source(history: dict[str, dict[str, list[float]]], regime: str) -> str:
    """Select raw/calibrated using only previously completed test folds."""
    prior = history.get(regime)
    if not prior or not prior["raw_brier"] or not prior["calibrated_brier"]:
        return "raw"
    raw = float(np.mean(prior["raw_brier"]))
    calibrated = float(np.mean(prior["calibrated_brier"]))
    return "calibrated" if calibrated < raw else "raw"


def _regime_metrics(
    y_test: pd.Series,
    raw_probability: np.ndarray,
    calibrated_probability: np.ndarray,
    regimes: pd.Series,
    history: dict[str, dict[str, list[float]]],
) -> tuple[RegimeMetrics, ...]:
    metrics: list[RegimeMetrics] = []
    for regime in ("low_vol", "high_vol"):
        mask = regimes.to_numpy() == regime
        if not np.any(mask):
            continue
        y = y_test.to_numpy()[mask]
        raw = raw_probability[mask]
        calibrated = calibrated_probability[mask]
        source = _selected_source(history, regime)
        selected = calibrated if source == "calibrated" else raw
        metrics.append(RegimeMetrics(
            regime=regime,
            test_rows=int(np.sum(mask)),
            raw_brier=float(brier_score_loss(y, raw)),
            calibrated_brier=float(brier_score_loss(y, calibrated)),
            selected_brier=float(brier_score_loss(y, selected)),
            raw_ece=_expected_calibration_error(y, raw),
            calibrated_ece=_expected_calibration_error(y, calibrated),
            selected_ece=_expected_calibration_error(y, selected),
            selected_source=source,
        ))
    return tuple(metrics)


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
    history: dict[str, dict[str, list[float]]] = {}
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
        raw_probability = model.predict_proba(X_test)[:, 1]
        pred = (raw_probability >= 0.5).astype(int)

        calibrated = _calibrated_model(len(X_train))
        calibrated.fit(X_train, y_train)
        calibrated_probability = calibrated.predict_proba(X_test)[:, 1]

        baseline = _baseline_predictions(X_test)
        regimes = _volatility_regime(X_train, X_test)
        fold_regime_metrics = _regime_metrics(
            y_test, raw_probability, calibrated_probability, regimes, history
        )

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
            raw_brier=float(brier_score_loss(y_test, raw_probability)),
            calibrated_brier=float(brier_score_loss(y_test, calibrated_probability)),
            raw_log_loss=float(log_loss(y_test, raw_probability, labels=[0, 1])),
            calibrated_log_loss=float(log_loss(y_test, calibrated_probability, labels=[0, 1])),
            raw_ece=_expected_calibration_error(y_test.to_numpy(), raw_probability),
            calibrated_ece=_expected_calibration_error(y_test.to_numpy(), calibrated_probability),
            regime_metrics=fold_regime_metrics,
            test_rows=len(X_test),
        ))

        for metric in fold_regime_metrics:
            bucket = history.setdefault(metric.regime, {"raw_brier": [], "calibrated_brier": []})
            bucket["raw_brier"].append(metric.raw_brier)
            bucket["calibrated_brier"].append(metric.calibrated_brier)

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
        raw_brier=float(np.mean([f.raw_brier for f in folds])),
        calibrated_brier=float(np.mean([f.calibrated_brier for f in folds])),
        raw_log_loss=float(np.mean([f.raw_log_loss for f in folds])),
        calibrated_log_loss=float(np.mean([f.calibrated_log_loss for f in folds])),
        raw_ece=float(np.mean([f.raw_ece for f in folds])),
        calibrated_ece=float(np.mean([f.calibrated_ece for f in folds])),
    )
