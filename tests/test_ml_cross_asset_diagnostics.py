import numpy as np
import pandas as pd
import pytest

from app.services.ml_cross_asset_diagnostics import (
    diagnose_predictions,
    expected_calibration_error,
    feature_distribution_shift,
)


def _series(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values), freq="D"))


def test_diagnose_predictions_reports_class_and_probability_bias() -> None:
    probability = _series([0.2, 0.8, 0.7, 0.4])
    target = _series([0, 1, 0, 1])
    prediction = _series([0, 1, 1, 0])

    result = diagnose_predictions(
        probability,
        target,
        prediction=prediction,
        fold_brier=[0.30, 0.20, 0.25],
        fold_ece=[0.20, 0.15, 0.10],
    )

    assert result.rows == 4
    assert result.actual_positive_rate == pytest.approx(0.5)
    assert result.predicted_positive_rate == pytest.approx(0.5)
    assert result.mean_probability == pytest.approx(0.525)
    assert result.probability_bias == pytest.approx(0.025)
    assert result.prediction_bias == pytest.approx(0.0)
    assert result.first_fold_brier == pytest.approx(0.30)
    assert result.last_fold_brier == pytest.approx(0.25)
    assert result.brier_temporal_delta == pytest.approx(-0.05)
    assert result.first_fold_ece == pytest.approx(0.20)
    assert result.last_fold_ece == pytest.approx(0.10)
    assert result.ece_temporal_delta == pytest.approx(-0.10)


def test_ece_is_zero_for_perfectly_calibrated_constant_probability() -> None:
    probability = _series([0.5, 0.5, 0.5, 0.5])
    target = _series([0, 1, 0, 1])

    assert expected_calibration_error(probability, target) == pytest.approx(0.0)


def test_feature_distribution_shift_is_causal_and_per_feature() -> None:
    reference = pd.DataFrame(
        {"ema_gap": [0.0, 0.1, 0.2], "rsi": [0.0, 0.0, 0.0]},
    )
    observed = pd.DataFrame(
        {"ema_gap": [0.3, 0.4, 0.5], "rsi": [0.0, 0.0, 0.0]},
    )

    result = feature_distribution_shift(reference, observed)

    assert result["by_feature"]["rsi"] == pytest.approx(0.0)
    assert result["by_feature"]["ema_gap"] > 0.0
    assert result["max_standardized_mean_shift"] == pytest.approx(
        result["by_feature"]["ema_gap"]
    )


def test_diagnostics_reject_invalid_probabilities() -> None:
    with pytest.raises(ValueError, match="probabilities must be in \[0, 1\]"):
        diagnose_predictions(_series([-0.1, 0.5]), _series([0, 1]))


def test_diagnostics_are_finite_for_normal_inputs() -> None:
    result = diagnose_predictions(
        _series([0.1, 0.4, 0.8, 0.9]),
        _series([0, 0, 1, 1]),
    )
    values = np.asarray(
        [result.accuracy, result.brier, result.ece, result.probability_bias],
        dtype=float,
    )
    assert np.isfinite(values).all()
