from __future__ import annotations

from unittest.mock import patch

from scripts.run_xgboost_oos_cost_attribution import SCENARIOS, run_symbol


def test_cost_attribution_keeps_same_oos_contract_across_scenarios() -> None:
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
            import pandas as pd
            return pd.Series([100_000.0, 90_000.0])

    class OOS:
        folds = 7
        test_rows = 700
        probabilities = __import__("pandas").Series(
            [0.6],
            index=__import__("pandas").date_range("2025-01-01", periods=1, tz="UTC"),
        )

    def fake_load(*args, **kwargs):
        import pandas as pd
        return pd.DataFrame(index=pd.date_range("2021-01-01", periods=2, tz="UTC")), Quality()

    def fake_backtest(history, **kwargs):
        assert kwargs["threshold"] == 0.60
        assert kwargs["horizon"] == 5
        assert kwargs["train_size"] == 500
        assert kwargs["test_size"] == 100
        assert kwargs["step"] == 100
        return OOS(), Result()

    with patch("scripts.run_xgboost_oos_cost_attribution.load_market_history", side_effect=fake_load),          patch("scripts.run_xgboost_oos_cost_attribution.run_xgboost_oos_backtest", side_effect=fake_backtest):
        rows = run_symbol("PETR4", initial_cash=100_000.0, horizon=5, train_size=500, test_size=100, step=100, threshold=0.60)

    assert len(rows) == len(SCENARIOS)
    assert {row["oos_folds"] for row in rows} == {7}
    assert {row["oos_rows"] for row in rows} == {700}
    assert {row["threshold"] for row in rows} == {0.60}
