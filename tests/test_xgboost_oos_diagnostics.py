from __future__ import annotations

import pandas as pd
import pytest

from app.services.xgboost_oos import XGBoostOOSRun
from app.services.xgboost_oos_diagnostics import diagnose_xgboost_oos_signals


def _oos(probabilities: list[float], index: pd.DatetimeIndex) -> XGBoostOOSRun:
    p = pd.Series(probabilities, index=index, name="probability")
    pred = p.ge(0.5).astype(int).rename("prediction")
    return XGBoostOOSRun(
        predictions=pred,
        probabilities=p,
        test_rows=len(p),
        folds=1,
        fold_metadata=(),
    )


def test_signal_diagnostics_counts_entries_exits_and_holding_periods():
    index = pd.date_range("2026-01-01", periods=8, freq="D")
    history = pd.DataFrame({"Close": range(100, 108)}, index=index)
    oos = _oos([0.40, 0.65, 0.70, 0.55, 0.61, 0.59, 0.62, 0.40], index)

    result = diagnose_xgboost_oos_signals(history, symbol="TEST", oos=oos, threshold=0.60)

    assert result.active_ratio == pytest.approx(4 / 8)
    assert result.signal_entries == 3
    assert result.signal_exits == 3
    assert result.signal_transitions == 6
    assert result.holding_periods_bars == (2, 1, 1)
    assert result.symbol == "TEST"


def test_entry_holding_analysis_exposes_counterfactual_horizons():
    index = pd.date_range("2026-01-01", periods=12, freq="D")
    history = pd.DataFrame({"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]}, index=index)
    oos = _oos([0.40, 0.65, 0.55, 0.40, 0.70, 0.68, 0.55, 0.40, 0.61, 0.59, 0.40, 0.40], index)

    result = diagnose_xgboost_oos_signals(history, symbol="TEST", oos=oos, threshold=0.60)

    assert len(result.entry_holding_analysis) == 3
    first = result.entry_holding_analysis[0]
    assert first["actual_holding_bars"] == 1
    assert first["actual_exit_return"] == pytest.approx(0.0)
    assert first["future_return_3d"] == pytest.approx(104 / 101 - 1.0)
    assert first["future_return_5d"] == pytest.approx(106 / 101 - 1.0)
    assert first["future_return_10d"] == pytest.approx(111 / 101 - 1.0)


def test_probability_bins_expose_forward_returns_without_dropping_probability_rows():
    index = pd.date_range("2026-01-01", periods=15, freq="D")
    history = pd.DataFrame({"close": [100 + i for i in range(15)]}, index=index)
    probabilities = [0.50, 0.52, 0.57, 0.62, 0.67, 0.72, 0.77, 0.82, 0.92, 0.48, 0.54, 0.59, 0.64, 0.69, 0.74]
    oos = _oos(probabilities, index)

    result = diagnose_xgboost_oos_signals(history, symbol="TEST", oos=oos, threshold=0.60)

    assert sum(row["rows"] for row in result.probability_bins) == len(probabilities)
    assert len(result.probability_bins) == 9
    assert result.conditional_returns["long"]["rows"] == 9
    assert result.conditional_returns["cash"]["rows"] == 6
    assert result.conditional_returns["long"]["future_return_5d_rows"] == 6


def test_diagnostics_reject_invalid_threshold():
    index = pd.date_range("2026-01-01", periods=6, freq="D")
    history = pd.DataFrame({"close": range(100, 106)}, index=index)
    oos = _oos([0.4] * 6, index)

    with pytest.raises(ValueError, match="threshold"):
        diagnose_xgboost_oos_signals(history, symbol="TEST", oos=oos, threshold=1.0)
