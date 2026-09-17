import pandas as pd
import pytest

from scripts.run_ml_robustness_audit import (
    _oos_replay_window,
    probability_to_long_only_signals,
    yearly_metrics,
)

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

def test_provider_ohlcv_columns_are_normalized_before_oos_replay() -> None:
    index = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0, 13.0, 14.0],
            "High": [11.0, 12.0, 13.0, 14.0, 15.0],
            "Low": [9.0, 10.0, 11.0, 12.0, 13.0],
            "Close": [10.5, 11.5, 12.5, 13.5, 14.5],
            "Volume": [1000, 1100, 1200, 1300, 1400],
            "Dividend": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
        index=index,
    )

    replay_frame = frame.rename(
        columns={column: str(column).lower() for column in frame.columns}
    )
    probabilities = pd.Series(
        [0.60, 0.65],
        index=index[1:3],
    )

    result = _oos_replay_window(replay_frame, probabilities)

    assert list(result.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "dividend",
    ]
    assert result.index[0] == index[1]
    assert result.index[-1] == index[3]
