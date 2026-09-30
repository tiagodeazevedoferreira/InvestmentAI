from types import SimpleNamespace

import pandas as pd
import pytest

from scripts.run_ml_model_diagnosis import (
    _brier_score,
    _calibration_buckets,
    _fold_performance,
    _quantiles,
)


def test_quantiles_are_deterministic() -> None:
    values = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
    result = _quantiles(values)
    assert result["p50"] == pytest.approx(0.3)
    assert result["p05"] == pytest.approx(0.12)
    assert result["p95"] == pytest.approx(0.48)


def test_brier_score_is_zero_for_perfect_probabilities() -> None:
    probabilities = pd.Series([0.0, 1.0, 0.0, 1.0])
    target = pd.Series([0, 1, 0, 1])
    assert _brier_score(probabilities, target) == pytest.approx(0.0)


def test_calibration_buckets_preserve_observed_rate() -> None:
    probabilities = pd.Series([0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
    target = pd.Series([0, 1, 0, 1, 1, 0])
    result = _calibration_buckets(probabilities, target)
    assert len(result) == 6
    assert result[1]["mean_probability"] == pytest.approx(0.55)
    assert result[1]["observed_positive_rate"] == pytest.approx(1.0)


def test_fold_performance_includes_roc_auc_and_pr_auc() -> None:
    index = pd.date_range(
        "2026-01-01",
        periods=6,
        freq="D",
    )

    probabilities = pd.Series(
        [0.05, 0.15, 0.85, 0.95, 0.20, 0.80],
        index=index,
    )

    target = pd.Series(
        [0, 0, 1, 1, 0, 1],
        index=index,
    )

    fold = SimpleNamespace(
        fold=1,
        test_start=index[0],
        test_end=index[-1],
    )

    result = _fold_performance(
        probabilities,
        target,
        [fold],
    )

    assert len(result) == 1

    metrics = result[0]

    assert metrics["roc_auc"] == pytest.approx(1.0)
    assert metrics["pr_auc"] == pytest.approx(1.0)
    assert metrics["accuracy"] == pytest.approx(1.0)
    assert metrics["brier_score"] == pytest.approx(0.021666666666666667)


def test_fold_performance_returns_none_auc_for_single_class_fold() -> None:
    index = pd.date_range(
        "2026-02-01",
        periods=4,
        freq="D",
    )

    probabilities = pd.Series(
        [0.20, 0.30, 0.40, 0.45],
        index=index,
    )

    target = pd.Series(
        [0, 0, 0, 0],
        index=index,
    )

    fold = SimpleNamespace(
        fold=1,
        test_start=index[0],
        test_end=index[-1],
    )

    result = _fold_performance(
        probabilities,
        target,
        [fold],
    )

    assert len(result) == 1

    metrics = result[0]

    assert metrics["roc_auc"] is None
    assert metrics["pr_auc"] is None
