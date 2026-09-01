import pandas as pd
import pytest

from scripts.run_ml_model_diagnosis import _brier_score, _calibration_buckets, _quantiles


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
