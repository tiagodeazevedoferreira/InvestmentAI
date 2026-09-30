import pandas as pd
import pytest

from app.services.xgboost_signal_persistence import probabilities_to_persistent_signals


def _series(values):
    return pd.Series(values, index=pd.date_range("2026-01-01", periods=len(values), freq="D"))


def test_confirmation_requires_consecutive_entry_bars():
    result = probabilities_to_persistent_signals(_series([0.7, 0.4, 0.7, 0.7]), entry_threshold=0.6, confirmation_bars=2)
    assert result.tolist() == [-1, -1, -1, 1]


def test_confirmation_requires_consecutive_exit_bars():
    result = probabilities_to_persistent_signals(_series([0.7, 0.7, 0.5, 0.7, 0.5, 0.5]), entry_threshold=0.6, exit_threshold=0.55, confirmation_bars=2)
    assert result.tolist() == [-1, 1, 1, 1, 1, -1]


def test_hysteresis_enters_above_entry_and_holds_between_thresholds():
    result = probabilities_to_persistent_signals(_series([0.8, 0.6, 0.56, 0.54]), entry_threshold=0.7, exit_threshold=0.55)
    assert result.tolist() == [1, 1, 1, -1]


@pytest.mark.parametrize("kwargs", [
    {"entry_threshold": -0.1},
    {"entry_threshold": 1.1},
    {"exit_threshold": -0.1},
    {"confirmation_bars": 0},
])
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        probabilities_to_persistent_signals(_series([0.5, 0.6]), **kwargs)
