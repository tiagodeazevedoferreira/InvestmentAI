from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import run_xgboost_oos_backtest


SCENARIOS = {
    "zero_cost": (0.0, 0.0),
    "commission_only": (0.001, 0.0),
    "slippage_only": (0.0, 5.0),
    "commission_plus_slippage": (0.001, 5.0),
}


def _max_drawdown(equity) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def run_symbol(symbol: str, *, initial_cash: float, horizon: int, train_size: int, test_size: int, step: int, threshold: float) -> list[dict]:
    history, quality = load_market_history(
        symbol, source="provider", start="2021-09-15", end="2026-09-15", interval="1d"
    )
    rows = []
    for scenario, (commission_rate, slippage_bps) in SCENARIOS.items():
        config = BacktestConfig(
            initial_cash=initial_cash,
            commission_rate=commission_rate,
            slippage_bps=slippage_bps,
        )
        oos, result = run_xgboost_oos_backtest(
            history,
            symbol=symbol,
            horizon=horizon,
            train_size=train_size,
            test_size=test_size,
            step=step,
            threshold=threshold,
            backtest_config=config,
        )
        strategy_return = result.final_cash / initial_cash - 1.0
        rows.append(
            {
                "symbol": symbol,
                "scenario": scenario,
                "commission_rate": commission_rate,
                "slippage_bps": slippage_bps,
                "rows": int(len(history)),
                "quality_valid": bool(quality.valid),
                "oos_folds": oos.folds,
                "oos_rows": oos.test_rows,
                "oos_start": oos.probabilities.index.min().isoformat(),
                "oos_end": oos.probabilities.index.max().isoformat(),
                "threshold": threshold,
                "initial_cash": initial_cash,
                "final_cash": result.final_cash,
                "strategy_return": strategy_return,
                "max_drawdown": _max_drawdown(result.equity),
                "trades": result.trades,
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
                "final_position": result.final_position,
            }
        )
    zero = next(row for row in rows if row["scenario"] == "zero_cost")
    for row in rows:
        row["cost_impact_vs_zero_cost"] = row["strategy_return"] - zero["strategy_return"]
        row["cash_impact_vs_zero_cost"] = row["final_cash"] - zero["final_cash"]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--output", default="artifacts/xgboost-oos-cost-attribution/report.json")
    args = parser.parse_args()

    reports = []
    for symbol in CI_SYMBOLS:
        reports.extend(
            run_symbol(
                symbol,
                initial_cash=args.initial_cash,
                horizon=args.horizon,
                train_size=args.train_size,
                test_size=args.test_size,
                step=args.step,
                threshold=args.threshold,
            )
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2, default=str), encoding="utf-8")
    print(json.dumps(reports, indent=2, default=str))


if __name__ == "__main__":
    main()
