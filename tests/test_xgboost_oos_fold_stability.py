from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from app.services.xgboost_oos import XGBoostOOSFold, XGBoostOOSRun
from scripts.run_xgboost_oos_fold_stability import (
    COMBINED_COST,
    ZERO_COST,
    _build_fold_oos,
    _fold_rows,
)


def _oos_fixture() -> XGBoostOOSRun:
    index = pd.date_range("2025-01-01", periods=200, tz="UTC")
    probabilities = pd.Series([0.6 if i % 2 == 0 else 0.4 for i in range(200)], index=index)
    predictions = pd.Series([1 if i % 2 == 0 else 0 for i in range(200)], index=index)
    folds = (
        XGBoostOOSFold(1, index[0], index[99], index[0], index[99]),
        XGBoostOOSFold(2, index[100], index[199], index[100], index[199]),
    )
    return XGBoostOOSRun(
        predictions=predictions,
        probabilities=probabilities,
        test_rows=6,
        folds=2,
        fold_metadata=folds,
    )


def test_build_fold_oos_preserves_only_requested_fold() -> None:
    oos = _oos_fixture()
    fold = oos.fold_metadata[1]

    sliced = _build_fold_oos(oos, fold)

    assert sliced.folds == 1
    assert sliced.test_rows == 3
    assert sliced.probabilities.index.equals(oos.probabilities.index[100:])
    assert sliced.predictions.index.equals(oos.predictions.index[100:])
    assert sliced.fold_metadata == (fold,)


def test_fold_rows_reuses_same_source_oos_predictions() -> None:
    oos = _oos_fixture()
    history = pd.DataFrame(
        {
            "Open": [10.0] * 201,
            "High": [11.0] * 201,
            "Low": [9.0] * 201,
            "Close": [10.0 + (i % 3) for i in range(201)],
            "Volume": [100.0] * 201,
        },
        index=pd.date_range("2025-01-01", periods=201, tz="UTC"),
    )
    captured = []

    def fake_replay(history, *, symbol, oos, threshold, backtest_config):
        captured.append(oos)
        class Result:
            final_cash = 100_000.0
            final_position = 0.0
            trades = 2
            total_commission = backtest_config.commission_rate * 1000
            total_slippage = backtest_config.slippage_bps * 10
            equity = pd.Series([100_000.0, 99_000.0, 100_000.0], index=history.index[:3])
        return Result()

    with patch(
        "scripts.run_xgboost_oos_fold_stability.backtest_xgboost_oos_run",
        side_effect=fake_replay,
    ):
        rows = _fold_rows(
            history,
            symbol="PETR4",
            oos=oos,
            threshold=0.60,
            initial_cash=100_000.0,
        )

    assert len(rows) == 4
    assert all(candidate is not oos for candidate in captured)
    assert len({id(candidate) for candidate in captured}) == 2
    assert rows[0]["scenario"] == ZERO_COST
    assert rows[2]["scenario"] == COMBINED_COST
    assert {row["fold"] for row in rows} == {1, 2}
