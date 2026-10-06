from __future__ import annotations

from scripts.run_xgboost_oos_predictive_economic_diagnosis import evaluate


def _signal(symbol: str, long_mean: float, cash_mean: float) -> dict:
    return {
        "symbol": symbol,
        "oos_rows": 100,
        "threshold": 0.60,
        "conditional_returns": {
            "long": {"rows": 50, "future_return_5d_mean": long_mean},
            "cash": {"rows": 50, "future_return_5d_mean": cash_mean},
        },
    }


def _economic(symbol: str, strategy_return: float) -> dict:
    return {"symbol": symbol, "strategy_return": strategy_return}


def _cost(symbol: str, strategy_return: float, scenario: str) -> dict:
    return {
        "symbol": symbol,
        "scenario": scenario,
        "strategy_return": strategy_return,
    }


def _cost_pair(symbol: str, zero_cost: float, after_cost: float) -> list[dict]:
    return [
        _cost(symbol, zero_cost, "zero_cost"),
        _cost(symbol, after_cost, "commission_plus_slippage"),
    ]


def test_diagnosis_identifies_predictive_signal_but_cost_unviable() -> None:
    signals = [
        _signal("PETR4", 0.04, 0.01),
        _signal("VALE3", 0.03, 0.01),
        _signal("ITUB4", 0.01, 0.02),
    ]
    economic = [
        _economic("PETR4", 0.01),
        _economic("VALE3", -0.02),
        _economic("ITUB4", -0.03),
    ]
    costs = []
    costs.extend(_cost_pair("PETR4", 0.08, 0.01))
    costs.extend(_cost_pair("VALE3", 0.02, -0.02))
    costs.extend(_cost_pair("ITUB4", -0.03, -0.03))

    result = evaluate(signals, economic, costs)

    assert result["summary"]["symbols_with_positive_predictive_spread"] == 2
    assert result["summary"]["symbols_with_positive_zero_cost_strategy_return"] == 2
    assert result["summary"]["symbols_with_positive_after_cost_strategy_return"] == 1
    assert result["symbols"][0]["diagnosis"] == "positive_predictive_spread_and_positive_after_cost"
    assert result["symbols"][1]["diagnosis"] == "predictive_signal_but_cost_unviable"
    assert result["symbols"][2]["diagnosis"] == "no_positive_5d_long_vs_cash_spread"


def test_diagnosis_rejects_economic_cost_drift() -> None:
    signals = [_signal(symbol, 0.03, 0.01) for symbol in ("PETR4", "VALE3", "ITUB4")]
    economic = [_economic(symbol, 0.05) for symbol in ("PETR4", "VALE3", "ITUB4")]
    costs = []
    costs.extend(_cost_pair("PETR4", 0.08, 0.04))
    costs.extend(_cost_pair("VALE3", 0.08, 0.04))
    costs.extend(_cost_pair("ITUB4", 0.08, 0.04))

    try:
        evaluate(signals, economic, costs)
    except ValueError as exc:
        assert "drift" in str(exc)
    else:
        raise AssertionError("expected report drift failure")


def test_diagnosis_ignores_other_cost_scenarios() -> None:
    signals = [_signal(symbol, 0.03, 0.01) for symbol in ("PETR4", "VALE3", "ITUB4")]
    economic = [_economic(symbol, 0.04) for symbol in ("PETR4", "VALE3", "ITUB4")]
    costs = []
    for symbol in ("PETR4", "VALE3", "ITUB4"):
        costs.extend([
            _cost(symbol, 0.08, "zero_cost"),
            _cost(symbol, 0.05, "commission_only"),
            _cost(symbol, 0.045, "slippage_only"),
            _cost(symbol, 0.04, "commission_plus_slippage"),
        ])

    result = evaluate(signals, economic, costs)

    assert result["summary"]["symbols_with_positive_after_cost_strategy_return"] == 3
    assert all(row["after_cost_strategy_return"] == 0.04 for row in result["symbols"])
