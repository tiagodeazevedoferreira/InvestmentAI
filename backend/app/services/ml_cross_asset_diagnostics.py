from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PredictionDiagnostics:
    rows: int
    actual_positive_rate: float
    predicted_positive_rate: float
    mean_probability: float
    probability_bias: float
    prediction_bias: float
    accuracy: float
    brier: float
    ece: float
    first_fold_brier: float | None
    last_fold_brier: float | None
    brier_temporal_delta: float | None
    first_fold_ece: float | None
    last_fold_ece: float | None
    ece_temporal_delta: float | None

    def to_dict(self) -> dict[str, float | int | None]:
        return asdict(self)


def brier_score(probability: pd.Series, target: pd.Series) -> float:
    probability, target = _aligned(probability, target)
    return float(np.mean((probability.to_numpy() - target.to_numpy(dtype=float)) ** 2))


def expected_calibration_error(
    probability: pd.Series,
    target: pd.Series,
    *,
    bins: int = 10,
) -> float:
    if bins < 2:
        raise ValueError("bins must be at least 2")
    probability, target = _aligned(probability, target)
    p = probability.to_numpy(dtype=float)
    y = target.to_numpy(dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(y)
    error = 0.0
    for i in range(bins):
        if i == bins - 1:
            mask = (p >= edges[i]) & (p <= edges[i + 1])
        else:
            mask = (p >= edges[i]) & (p < edges[i + 1])
        if not mask.any():
            continue
        error += float(mask.mean()) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(error)


def diagnose_predictions(
    probability: pd.Series,
    target: pd.Series,
    *,
    prediction: pd.Series | None = None,
    fold_brier: list[float] | None = None,
    fold_ece: list[float] | None = None,
    bins: int = 10,
) -> PredictionDiagnostics:
    probability, target = _aligned(probability, target)
    p = probability.to_numpy(dtype=float)
    y = target.to_numpy(dtype=int)
    predicted = (p >= 0.5).astype(int) if prediction is None else _aligned(prediction, target)[0].to_numpy(dtype=int)

    actual_rate = float(y.mean())
    predicted_rate = float(predicted.mean())
    mean_probability = float(p.mean())
    return PredictionDiagnostics(
        rows=len(y),
        actual_positive_rate=actual_rate,
        predicted_positive_rate=predicted_rate,
        mean_probability=mean_probability,
        probability_bias=mean_probability - actual_rate,
        prediction_bias=predicted_rate - actual_rate,
        accuracy=float(np.mean(predicted == y)),
        brier=brier_score(probability, target),
        ece=expected_calibration_error(probability, target, bins=bins),
        first_fold_brier=_first(fold_brier),
        last_fold_brier=_last(fold_brier),
        brier_temporal_delta=_delta(fold_brier),
        first_fold_ece=_first(fold_ece),
        last_fold_ece=_last(fold_ece),
        ece_temporal_delta=_delta(fold_ece),
    )


def feature_distribution_shift(
    reference: pd.DataFrame,
    observed: pd.DataFrame,
) -> dict[str, float | dict[str, float]]:
    """Report standardized mean shifts between a causal reference and OOS data.

    The reference frame must contain only observations available before the OOS
    window. The metric is descriptive: it is not a model-promotion criterion.
    """
    if reference.empty or observed.empty:
        raise ValueError("reference and observed feature frames must be non-empty")
    columns = [column for column in reference.columns if column in observed.columns]
    if not columns:
        raise ValueError("reference and observed frames have no common features")

    shifts: dict[str, float] = {}
    for column in columns:
        a = pd.to_numeric(reference[column], errors="coerce").dropna().to_numpy(dtype=float)
        b = pd.to_numeric(observed[column], errors="coerce").dropna().to_numpy(dtype=float)
        if len(a) == 0 or len(b) == 0:
            continue
        pooled_std = float(np.sqrt((np.var(a) + np.var(b)) / 2.0))
        if pooled_std == 0.0:
            shifts[column] = 0.0 if float(np.mean(a)) == float(np.mean(b)) else float("inf")
        else:
            shifts[column] = abs(float(np.mean(b)) - float(np.mean(a))) / pooled_std

    if not shifts:
        raise ValueError("no numeric feature observations available")
    finite = [value for value in shifts.values() if np.isfinite(value)]
    return {
        "max_standardized_mean_shift": float(max(finite)) if finite else float("inf"),
        "mean_standardized_mean_shift": float(np.mean(finite)) if finite else float("inf"),
        "by_feature": shifts,
    }


def _aligned(first: pd.Series, second: pd.Series) -> tuple[pd.Series, pd.Series]:
    joined = pd.concat([first.rename("first"), second.rename("second")], axis=1).dropna()
    if joined.empty:
        raise ValueError("aligned inputs must contain at least one observation")
    probability = joined["first"].astype(float)
    target = joined["second"]
    if not np.isfinite(probability.to_numpy()).all():
        raise ValueError("probability values must be finite")
    if ((probability < 0.0) | (probability > 1.0)).any():
        raise ValueError("probabilities must be in [0, 1]")
    if not target.isin([0, 1]).all():
        raise ValueError("target values must be binary 0/1")
    return probability, target


def _first(values: list[float] | None) -> float | None:
    return None if not values else float(values[0])


def _last(values: list[float] | None) -> float | None:
    return None if not values else float(values[-1])


def _delta(values: list[float] | None) -> float | None:
    if not values:
        return None
    return float(values[-1] - values[0])
