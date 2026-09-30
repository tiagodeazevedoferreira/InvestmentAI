from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import backtest_xgboost_oos_run
from app.services.xgboost_oos_artifact import (
    load_xgboost_oos_artifact,
    validate_xgboost_oos_artifact_configuration,
)

DEFAULT_THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
COST_SCENARIOS = {
    "zero_cost": (0.0, 0.0),
    "commission_plus_slippage": (0.001, 5.0),
}


def _max_drawdown(equity) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _validate_thresholds(thresholds: tuple[float, ...]) -> tuple[float, ...]:
    if not thresholds:
        raise ValueError("at least one threshold is required")
    normalized = tuple(float(value) for value in thresholds)
    if any(value < 0.0 or value > 1.0 for value in normalized):
        raise ValueError("thresholds must be between 0 and 1")
    if len(set(normalized)) != len(normalized):
        raise ValueError("thresholds must be unique")
    return normalized


def run_symbol(
    symbol: str,
    *,
    initial_cash: float,
    horizon: int,
    train_size: int,
    test_size: int,
    step: int,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    oos_artifact_dir: str | None = None,
) -> list[dict]:
    thresholds = _validate_thresholds(thresholds)
    history, quality = load_market_history(
        symbol, source="provider", start="2021-09-15", end="2026-09-15", interval="1d"
    )
    expected_oos_configuration = {
        "requested_start": "2021-09-15",
        "requested_end": "2026-09-15",
        "horizon": horizon,
        "train_size": train_size,
        "test_size": test_size,
        "step": step,
        "threshold": 0.60,
        "initial_cash": initial_cash,
    }
    if not oos_artifact_dir:
        raise ValueError("economic sensitivity requires a shared OOS artifact directory")

    oos, payload = load_xgboost_oos_artifact(Path(oos_artifact_dir) / f"{symbol.upper()}.json")
    if str(payload.get("symbol", "")).upper() != symbol.upper():
        raise ValueError(f"OOS artifact symbol mismatch for {symbol}")
    validate_xgboost_oos_artifact_configuration(payload, expected_oos_configuration)

    rows: list[dict] = []
    for threshold in thresholds:
        for scenario, (commission_rate, slippage_bps) in COST_SCENARIOS.items():
            config = BacktestConfig(
                initial_cash=initial_cash,
                commission_rate=commission_rate,
                slippage_bps=slippage_bps,
            )
            result = backtest_xgboost_oos_run(
                history,
                symbol=symbol,
                oos=oos,
                threshold=threshold,
                backtest_config=config,
            )
            strategy_return = result.final_cash / initial_cash - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "threshold": threshold,
                    "scenario": scenario,
                    "commission_rate": commission_rate,
                    "slippage_bps": slippage_bps,
                    "rows": int(len(history)),
                    "quality_valid": bool(quality.valid),
                    "oos_folds": oos.folds,
                    "oos_rows": oos.test_rows,
                    "oos_start": oos.probabilities.index.min().isoformat(),
                    "oos_end": oos.probabilities.index.max().isoformat(),
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

    for threshold in thresholds:
        zero = next(
            row
            for row in rows
            if row["threshold"] == threshold and row["scenario"] == "zero_cost"
        )
        for row in rows:
            if row["threshold"] == threshold:
                row["cost_impact_vs_zero_cost"] = row["strategy_return"] - zero["strategy_return"]
                row["cash_impact_vs_zero_cost"] = row["final_cash"] - zero["final_cash"]

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run descriptive XGBoost OOS economic sensitivity without retraining or selecting a threshold."
    )
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--thresholds", nargs="+", type=float, default=list(DEFAULT_THRESHOLDS))
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--oos-artifact-dir", required=True)
    parser.add_argument("--output", default="artifacts/xgboost-oos-economic-sensitivity/report.json")
    args = parser.parse_args()

    thresholds = _validate_thresholds(tuple(args.thresholds))
    reports: list[dict] = []
    for symbol in CI_SYMBOLS:
        reports.extend(
            run_symbol(
                symbol,
                initial_cash=args.initial_cash,
                horizon=args.horizon,
                train_size=args.train_size,
                test_size=args.test_size,
                step=args.step,
                thresholds=thresholds,
                oos_artifact_dir=args.oos_artifact_dir,
            )
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2, default=str), encoding="utf-8")
    print(json.dumps(reports, indent=2, default=str))


if __name__ == "__main__":
    main()
