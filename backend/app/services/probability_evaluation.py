from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PairedMetricSummary:
    metric: str
    comparison: str
    n: int
    mean_delta: float
    median_delta: float
    win_rate: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float


def paired_fold_summary(
    baseline: list[float] | np.ndarray,
    candidate: list[float] | np.ndarray,
    *,
    metric: str,
    comparison: str,
    bootstrap_iterations: int = 4000,
    seed: int = 42,
) -> PairedMetricSummary:
    """Summarize paired OOS fold deltas with a deterministic bootstrap CI.

    Delta is candidate - baseline. For Brier/log-loss/ECE, a negative delta is
    an improvement. Resampling is performed over complete paired folds, never
    over individual observations, so the temporal dependence within a fold is
    preserved.
    """
    a = np.asarray(baseline, dtype=float)
    b = np.asarray(candidate, dtype=float)
    if a.ndim != 1 or b.ndim != 1 or len(a) != len(b) or len(a) < 2:
        raise ValueError("paired inputs must be one-dimensional arrays with equal length >= 2")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("paired inputs must contain only finite values")
    if bootstrap_iterations < 100:
        raise ValueError("bootstrap_iterations must be at least 100")

    delta = b - a
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(delta), size=(bootstrap_iterations, len(delta)))
    means = delta[samples].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])

    return PairedMetricSummary(
        metric=metric,
        comparison=comparison,
        n=len(delta),
        mean_delta=float(delta.mean()),
        median_delta=float(np.median(delta)),
        win_rate=float(np.mean(delta < 0.0)),
        bootstrap_ci_low=float(low),
        bootstrap_ci_high=float(high),
    )
