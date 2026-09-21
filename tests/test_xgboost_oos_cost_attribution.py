from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from scripts.run_xgboost_oos_cost_attribution import SCENARIOS, run_symbol


def test_cost_attribution_reuses_identical_oos_predictions_across_scenarios() -> None:
    class Quality:
        valid = True

    class Result:
        final_cash = 90_000.0
        trades = 10
        total_commission = 100.0
        total_slippage = 50.0
        final_position = 0.0

        @property
        def equity(self):
            return pd.Series([100_000.0, 90_000.0])

    oos_probabilities = pd.Series(
        [0.6],
        index=pd.date_range("2025-01-01", periods=1, tz="UTC"),
        name="probability",
    )

    class OOS:
        folds = 7
        test_rows = 700
        probabilities = oos_probabilities

    def fake_load(*args, **kwargs):
        return pd.DataFrame(index=pd.date_range("2021-01-01", periods=2, tz="UTC")), Quality()

    with (
        patch(
            "scripts.run_xgboost_oos_cost_attribution.load_market_history",
            side_effect=fake_load,
        ),
        patch(
            "scripts.run_xgboost_oos_cost_attribution.run_xgboost_oos_backtest",
            return_value=(OOS(), Result()),
        ) as train_call,
        patch(
            "scripts.run_xgboost_oos_cost_attribution.backtest_xgboost_oos_run",
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
            threshold=0.60,
        )

    assert len(rows) == len(SCENARIOS)
    assert train_call.call_count == 1
    assert replay_call.call_count == len(SCENARIOS)

    observed_oos = [call.kwargs["oos"] for call in replay_call.call_args_list]
    assert all(candidate is observed_oos[0] for candidate in observed_oos)

    for call in replay_call.call_args_list:
        assert call.kwargs["threshold"] == 0.60

    assert {row["oos_folds"] for row in rows} == {7}
    assert {row["oos_rows"] for row in rows} == {700}
    assert {row["threshold"] for row in rows} == {0.60}
