from __future__ import annotations

import pytest

from scripts.run_xgboost_oos_economic_verdict import evaluate


def _economic(symbol: str, strategy_return: float, benchmark_return: float, trades: int = 10) -> dict:
    return {
        "symbol": symbol,
        "threshold": 0.60,
        "quality_valid": True,
        "strategy_return": strategy_return,
        "benchmark_return": benchmark_return,
        "excess_return_vs_buy_hold": strategy_return - benchmark_return,
        "max_drawdown": -0.10,
        "trades": trades,
    }


def _persistence(symbol: str, strategy_return: float, trades: int = 10) -> dict:
    return {
        "symbol": symbol,
        "name": "baseline_060",
        "entry_threshold": 0.60,
        "exit_threshold": 0.60,
        "confirmation_bars": 1,
        "scenario": "commission_plus_slippage",
        "quality_valid": True,
        "strategy_return": strategy_return,
        "trades": trades,
    }


def test_verdict_requires_positive_after_cost_return_and_positive_benchmark_excess() -> None:
    economic = [
        _economic("PETR4", 0.10, 0.02),
        _economic("VALE3", 0.08, 0.03),
        _economic("ITUB4", 0.06, 0.01),
    ]
    persistence = [_persistence(row["symbol"], row["strategy_return"]) for row in economic]

    result = evaluate(economic, persistence)

    assert result["verdict"] == "PASS"
    assert result["failed_symbols"] == []
    assert result["model_promotion_allowed"] is True


def test_verdict_fails_when_any_symbol_does_not_clear_benchmark_after_costs() -> None:
    economic = [
        _economic("PETR4", 0.10, 0.02),
        _economic("VALE3", 0.08, 0.03),
        _economic("ITUB4", -0.01, 0.20),
    ]
    persistence = [_persistence(row["symbol"], row["strategy_return"]) for row in economic]

    result = evaluate(economic, persistence)

    assert result["verdict"] == "FAIL"
    assert result["failed_symbols"] == ["ITUB4"]
    assert result["model_promotion_allowed"] is False


def test_verdict_rejects_report_drift() -> None:
    economic = [_economic(symbol, 0.05, 0.01) for symbol in ("PETR4", "VALE3", "ITUB4")]
    persistence = [_persistence(row["symbol"], row["strategy_return"]) for row in economic]
    persistence[1]["strategy_return"] += 0.001

    with pytest.raises(ValueError, match="strategy return mismatch"):
        evaluate(economic, persistence)
