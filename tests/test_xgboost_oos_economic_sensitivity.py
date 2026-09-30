from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from scripts.run_xgboost_oos_economic_sensitivity import (
    COST_SCENARIOS,
    DEFAULT_THRESHOLDS,
    _validate_thresholds,
    run_symbol,
)


def test_threshold_validation_rejects_duplicates_and_out_of_range() -> None:
    assert _validate_thresholds((0.5, 0.6)) == (0.5, 0.6)
    for thresholds in ((0.5, 0.5), (-0.1, 0.6), (0.6, 1.1), ()):
        try:
            _validate_thresholds(thresholds)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {thresholds}")


def test_sensitivity_reuses_one_immutable_oos_run_across_thresholds_and_costs() -> None:
    class Quality:
        valid = True

    class Result:
        final_cash = 99_000.0
        trades = 8
        total_commission = 100.0
        total_slippage = 50.0
        final_position = 0.0

        @property
        def equity(self):
            return pd.Series([100_000.0, 99_000.0])

    class OOS:
        folds = 7
        test_rows = 700
        probabilities = pd.Series(
            [0.55], index=pd.date_range("2025-01-01", periods=1, tz="UTC"), name="probability"
        )

    def fake_load(*args, **kwargs):
        return pd.DataFrame(index=pd.date_range("2021-01-01", periods=2, tz="UTC")), Quality()

    oos = OOS()
    with (
        patch(
            "scripts.run_xgboost_oos_economic_sensitivity.load_market_history",
            side_effect=fake_load,
        ),
        patch(
            "scripts.run_xgboost_oos_economic_sensitivity.load_xgboost_oos_artifact",
            return_value=(oos, {"symbol": "PETR4"}),
        ),
        patch(
            "scripts.run_xgboost_oos_economic_sensitivity.validate_xgboost_oos_artifact_configuration",
        ) as validate_call,
        patch(
            "scripts.run_xgboost_oos_economic_sensitivity.backtest_xgboost_oos_run",
            return_value=Result(),
        ) as replay_call,
    ):
        rows = run_symbol(
            "PETR4",
            initial_cash=100_000.0,
            horizon=5,
            train_size=500,
            test_size=100,
            step=100,
            thresholds=(0.50, 0.60),
            oos_artifact_dir="artifacts/xgboost-oos-shared",
        )

    assert validate_call.call_count == 1
    assert len(rows) == 2 * len(COST_SCENARIOS)
    assert replay_call.call_count == len(rows)
    assert all(call.kwargs["oos"] is oos for call in replay_call.call_args_list)
    assert {call.kwargs["threshold"] for call in replay_call.call_args_list} == {0.50, 0.60}
    assert {row["threshold"] for row in rows} == {0.50, 0.60}
    assert {row["oos_folds"] for row in rows} == {7}
    assert {row["oos_rows"] for row in rows} == {700}


def test_default_threshold_grid_is_descriptive_and_stable() -> None:
    assert DEFAULT_THRESHOLDS == (0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
