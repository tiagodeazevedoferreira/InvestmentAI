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


def test_model_and_baseline_metrics_are_bounded():
    result = purged_walk_forward(market_frame(), "TEST", train_size=500, test_size=100, step=100)
    for value in (
        result.model_balanced_accuracy,
        result.model_macro_f1,
        result.baseline_balanced_accuracy,
        result.baseline_macro_f1,
    ):
        assert 0.0 <= value <= 1.0


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError):
        purged_walk_forward(market_frame(100), "TEST", train_size=500, test_size=100)
