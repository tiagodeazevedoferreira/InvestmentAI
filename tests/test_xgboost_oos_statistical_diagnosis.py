from __future__ import annotations

from scripts.run_xgboost_oos_statistical_diagnosis import evaluate


def _signal(symbol: str) -> dict:
    observations = []
    for index, value in enumerate((0.04, 0.03, 0.02, 0.05, 0.01, -0.01, 0.00, 0.02, 0.03, 0.01)):
        observations.append({"timestamp": f"2026-01-{index + 1:02d}", "regime": "long", "future_return_5d": value})
    for index, value in enumerate((0.01, 0.00, 0.01, -0.01, 0.00, 0.02, 0.01, 0.00, -0.01, 0.01)):
        observations.append({"timestamp": f"2026-02-{index + 1:02d}", "regime": "cash", "future_return_5d": value})
    return {"symbol": symbol, "conditional_return_observations_5d": observations}


def _cost(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "scenario": "commission_plus_slippage",
        "strategy_return": -0.10,
        "cost_impact_vs_zero_cost": -0.20,
        "initial_cash": 100000.0,
        "trades": 20,
        "total_commission": 1000.0,
        "total_slippage": 500.0,
    }


def test_statistical_diagnosis_is_deterministic_and_uses_oos_observations():
    signals = [_signal(symbol) for symbol in ("PETR4", "VALE3", "ITUB4")]
    costs = [_cost(symbol) for symbol in ("PETR4", "VALE3", "ITUB4")]

    first = evaluate(signals, costs)
    second = evaluate(signals, costs)

    assert first == second
    assert first["summary"]["symbols_with_positive_observed_spread"] == 3
    assert first["symbols"][0]["bootstrap_ci_excludes_zero"] is True
    assert first["symbols"][0]["average_transaction_cost_per_trade"] == 75.0


def test_statistical_diagnosis_requires_all_symbols():
    signals = [_signal(symbol) for symbol in ("PETR4", "VALE3", "ITUB4")]
    costs = [_cost("PETR4"), _cost("VALE3")]

    try:
        evaluate(signals, costs)
    except ValueError as exc:
        assert "exactly PETR4, VALE3 and ITUB4" in str(exc)
    else:
        raise AssertionError("expected symbol coverage failure")
