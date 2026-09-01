import pandas as pd
import pytest

from scripts.run_ml_robustness_audit import probability_to_long_only_signals, yearly_metrics


def test_probability_threshold_mapping() -> None:
    probabilities = pd.Series([0.49, 0.50, 0.55, 0.60])
    signals = probability_to_long_only_signals(probabilities, threshold=0.55)
    assert signals.tolist() == [-1, -1, 1, 1]


def test_probability_threshold_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        probability_to_long_only_signals(pd.Series([0.2, 0.8]), threshold=0.4)
    with pytest.raises(ValueError):
        probability_to_long_only_signals(pd.Series([0.2, 1.2]), threshold=0.5)


def test_yearly_metrics_is_deterministic() -> None:
    index = pd.date_range("2023-01-01", periods=6, freq="YE")
    equity = pd.Series([100.0, 120.0, 108.0, 140.0, 126.0, 151.2], index=index)
    result = yearly_metrics(equity)
    assert result["positive_years"] == 3
    assert result["negative_years"] == 2
    assert result["best_year"] == pytest.approx(140 / 108 - 1)
    assert 0 < result["return_concentration"] <= 1
