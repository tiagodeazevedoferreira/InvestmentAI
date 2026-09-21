from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import (
    XGBoostOOSRun,
    backtest_xgboost_oos_run,
    run_xgboost_oos_backtest,
)


ZERO_COST = "zero_cost"
COMBINED_COST = "commission_plus_slippage"
SCENARIOS = {
    ZERO_COST: (0.0, 0.0),
    COMBINED_COST: (0.001, 5.0),
}


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def _build_fold_oos(oos: XGBoostOOSRun, fold) -> XGBoostOOSRun:
    probabilities = oos.probabilities.loc[fold.test_start : fold.test_end].copy()
    predictions = oos.predictions.loc[fold.test_start : fold.test_end].copy()
    if len(probabilities) != len(predictions):
        raise ValueError(f"fold {fold.fold} predictions/probabilities lengths differ")
    if len(probabilities) != 100:
        raise ValueError(f"fold {fold.fold} does not contain exactly 100 OOS rows")
    if not probabilities.index.equals(predictions.index):
        raise ValueError(f"fold {fold.fold} predictions/probabilities indexes differ")
    return XGBoostOOSRun(
        predictions=predictions,
        probabilities=probabilities,
        test_rows=len(probabilities),
        folds=1,
        fold_metadata=(fold,),
    )


def _fold_rows(history: pd.DataFrame, *, symbol: str, oos: XGBoostOOSRun, threshold: float, initial_cash: float) -> list[dict]:
    rows: list[dict] = []
    for fold in oos.fold_metadata:
        fold_oos = _build_fold_oos(oos, fold)
        for scenario, (commission_rate, slippage_bps) in SCENARIOS.items():
            config = BacktestConfig(
                initial_cash=initial_cash,
                commission_rate=commission_rate,
                slippage_bps=slippage_bps,
            )
            result = backtest_xgboost_oos_run(
                history,
                symbol=symbol,
                oos=fold_oos,
                threshold=threshold,
                backtest_config=config,
            )
            rows.append({
                "symbol": symbol,
                "fold": fold.fold,
                "scenario": scenario,
                "train_start": fold.train_start.isoformat(),
                "train_end": fold.train_end.isoformat(),
                "test_start": fold.test_start.isoformat(),
                "test_end": fold.test_end.isoformat(),
                "test_rows": fold_oos.test_rows,
                "threshold": threshold,
                "initial_cash": initial_cash,
                "final_cash": result.final_cash,
                "fold_return": result.final_cash / initial_cash - 1.0,
                "max_drawdown": _max_drawdown(result.equity),
                "trades": result.trades,
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
                "final_position": result.final_position,
            })
    return rows


def _summary(rows: list[dict]) -> dict:
    frame = pd.DataFrame(rows)
    summary: dict = {}
    for symbol in sorted(frame["symbol"].unique()):
        symbol_frame = frame[frame["symbol"] == symbol]
        summary[symbol] = {}
        for scenario in SCENARIOS:
            values = symbol_frame.loc[symbol_frame["scenario"] == scenario, "fold_return"].astype(float)
            positive = int((values > 0).sum())
            negative = int((values < 0).sum())
            zero = int((values == 0).sum())
            summary[symbol][scenario] = {
                "folds": int(values.size),
                "positive_folds": positive,
                "negative_folds": negative,
                "zero_return_folds": zero,
                "mean_fold_return": float(values.mean()),
                "median_fold_return": float(values.median()),
                "min_fold_return": float(values.min()),
                "max_fold_return": float(values.max()),
                "std_fold_return": float(values.std(ddof=0)),
                "sum_fold_returns": float(values.sum()),
                "absolute_return_sum": float(values.abs().sum()),
                "positive_return_sum": float(values[values > 0].sum()),
                "negative_return_sum": float(values[values < 0].sum()),
            }
    return summary


def run_symbol(symbol: str, *, initial_cash: float, horizon: int, train_size: int, test_size: int, step: int, threshold: float) -> tuple[list[dict], dict]:
    history, quality = load_market_history(symbol, source="provider", start="2021-09-15", end="2026-09-15", interval="1d")
    baseline_config = BacktestConfig(initial_cash=initial_cash)
    oos, _ = run_xgboost_oos_backtest(
        history,
        symbol=symbol,
        horizon=horizon,
        train_size=train_size,
        test_size=test_size,
        step=step,
        threshold=threshold,
        backtest_config=baseline_config,
    )
    rows = _fold_rows(history, symbol=symbol, oos=oos, threshold=threshold, initial_cash=initial_cash)
    symbol_summary = _summary(rows)
    return rows, {
        "symbol": symbol,
        "rows": len(history),
        "quality_valid": bool(quality.valid),
        "oos_folds": oos.folds,
        "oos_rows": oos.test_rows,
        "oos_start": oos.probabilities.index.min().isoformat(),
        "oos_end": oos.probabilities.index.max().isoformat(),
        "summary": symbol_summary[symbol],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--output", default="artifacts/xgboost-oos-fold-stability/report.json")
    args = parser.parse_args()

    all_rows: list[dict] = []
    summaries: list[dict] = []
    for symbol in CI_SYMBOLS:
        rows, summary = run_symbol(symbol, initial_cash=args.initial_cash, horizon=args.horizon, train_size=args.train_size, test_size=args.test_size, step=args.step, threshold=args.threshold)
        all_rows.extend(rows)
        summaries.append(summary)

    report = {
        "configuration": {
            "symbols": list(CI_SYMBOLS),
            "requested_start": "2021-09-15",
            "requested_end": "2026-09-15",
            "horizon": args.horizon,
            "train_size": args.train_size,
            "test_size": args.test_size,
            "step": args.step,
            "threshold": args.threshold,
            "initial_cash": args.initial_cash,
            "scenarios": SCENARIOS,
        },
        "folds": all_rows,
        "summaries": summaries,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
