import numpy as np
import pandas as pd
import pytest

from backend.app.services.walk_forward import purged_walk_forward


def market_frame(n=900):
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    trend = np.linspace(100, 160, n) + np.sin(np.arange(n) / 8) * 2
    return pd.DataFrame({
        "Open": trend,
        "High": trend + 1,
        "Low": trend - 1,
        "Close": trend,
        "Volume": np.full(n, 1000.0),
    }, index=idx)


def test_walk_forward_is_chronological_and_purged():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    assert len(result.folds) >= 2
    for fold in result.folds:
        assert pd.Timestamp(fold.train_end) < pd.Timestamp(fold.test_start)
        assert fold.test_rows == 100
        assert sum(metric.test_rows for metric in fold.regime_metrics) == fold.test_rows


def test_model_and_baseline_metrics_are_bounded():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    for value in (
        result.model_balanced_accuracy,
        result.model_macro_f1,
        result.baseline_balanced_accuracy,
        result.baseline_macro_f1,
        result.raw_brier,
        result.calibrated_brier,
        result.selected_brier,
        result.raw_log_loss,
        result.calibrated_log_loss,
        result.raw_ece,
        result.calibrated_ece,
        result.selected_ece,
    ):
        assert np.isfinite(value)
        assert value >= 0.0
    for value in (result.raw_brier, result.calibrated_brier, result.selected_brier, result.raw_ece, result.calibrated_ece, result.selected_ece):
        assert value <= 1.0


def test_calibration_is_evaluated_out_of_sample():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    assert all(fold.calibrated_brier >= 0.0 for fold in result.folds)
    assert all(fold.calibrated_log_loss >= 0.0 for fold in result.folds)
    assert all(fold.calibrated_ece >= 0.0 for fold in result.folds)


def test_regime_selection_uses_prior_folds_only():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    first_sources = {metric.selected_source for metric in result.folds[0].regime_metrics}
    assert first_sources == {"raw"}
    for fold in result.folds[1:]:
        for metric in fold.regime_metrics:
            assert metric.selected_source in {"raw", "calibrated"}
            for value in (
                metric.raw_brier,
                metric.calibrated_brier,
                metric.selected_brier,
                metric.raw_ece,
                metric.calibrated_ece,
                metric.selected_ece,
            ):
                assert np.isfinite(value)
                assert value >= 0.0
                assert value <= 1.0


def test_probability_aggregates_are_row_weighted_across_oos_folds():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    total_rows = sum(fold.test_rows for fold in result.folds)

    for field, aggregate in (
        ("raw_brier", result.raw_brier),
        ("calibrated_brier", result.calibrated_brier),
        ("raw_log_loss", result.raw_log_loss),
        ("calibrated_log_loss", result.calibrated_log_loss),
        ("raw_ece", result.raw_ece),
        ("calibrated_ece", result.calibrated_ece),
    ):
        expected = sum(getattr(fold, field) * fold.test_rows for fold in result.folds) / total_rows
        assert aggregate == pytest.approx(expected)

    expected_selected_brier = sum(
        metric.selected_brier * metric.test_rows
        for fold in result.folds
        for metric in fold.regime_metrics
    ) / total_rows
    expected_selected_ece = sum(
        metric.selected_ece * metric.test_rows
        for fold in result.folds
        for metric in fold.regime_metrics
    ) / total_rows
    assert result.selected_brier == pytest.approx(expected_selected_brier)
    assert result.selected_ece == pytest.approx(expected_selected_ece)


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError):
        purged_walk_forward(market_frame(100), "TEST", train_size=500, test_size=100)
