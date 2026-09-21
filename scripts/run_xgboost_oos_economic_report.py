from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.services.backtesting import BacktestConfig
from app.services.ci_market_data import CI_SYMBOLS, load_market_history
from app.services.xgboost_oos import backtest_xgboost_oos_run, run_xgboost_oos_backtest
from app.services.xgboost_oos_artifact import (
    load_xgboost_oos_artifact,
    validate_xgboost_oos_artifact_configuration,
)


def _buy_and_hold_return(history: pd.DataFrame, initial_cash: float) -> float:
    close = history["close"] if "close" in history.columns else history["Close"]
    return float(initial_cash * (close.iloc[-1] / close.iloc[0]))


def _oos_replay_window(history: pd.DataFrame, probabilities: pd.Series) -> pd.DataFrame:
    """Return the exact market window used by the economic backtest."""
    index = pd.DatetimeIndex(history.index)
    first_oos = pd.Timestamp(probabilities.index.min())
    last_oos = pd.Timestamp(probabilities.index.max())
    first_position = index.get_loc(first_oos)
    last_position = index.get_loc(last_oos)
    if not isinstance(first_position, (int, np.integer)) or not isinstance(last_position, (int, np.integer)):
        raise ValueError("history index lookup must resolve to unique positions")
    replay_end = last_position + 1
    if replay_end >= len(history):
        raise ValueError("history must contain a bar after the final OOS prediction")
    return history.iloc[first_position : replay_end + 1]


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def run_symbol(
    symbol: str,
    *,
    period: str,
    horizon: int,
    train_size: int,
    test_size: int,
    step: int,
    threshold: float,
    initial_cash: float,
    commission_rate: float,
    slippage_bps: float,
    oos_artifact_dir: str | None = None,
) -> dict:
    history, quality = load_market_history(
        symbol, source="provider", start="2021-09-15", end="2026-09-15", interval="1d"
    )
    config = BacktestConfig(
        initial_cash=initial_cash,
        commission_rate=commission_rate,
        slippage_bps=slippage_bps,
    )
    expected_oos_configuration = {
        "requested_start": "2021-09-15",
        "requested_end": "2026-09-15",
        "horizon": horizon,
        "train_size": train_size,
        "test_size": test_size,
        "step": step,
        "threshold": threshold,
        "initial_cash": initial_cash,
    }
    if oos_artifact_dir:
        oos, payload = load_xgboost_oos_artifact(
            Path(oos_artifact_dir) / f"{symbol.upper()}.json"
        )
        artifact_symbol = str(payload.get("symbol", "")).upper()
        if artifact_symbol != symbol.upper():
            raise ValueError(f"OOS artifact symbol mismatch: expected {symbol}, got {artifact_symbol}")
        validate_xgboost_oos_artifact_configuration(payload, expected_oos_configuration)
    else:
        oos, _ = run_xgboost_oos_backtest(
            history,
            symbol=symbol,
            horizon=horizon,
            train_size=train_size,
            test_size=test_size,
            step=step,
            threshold=threshold,
            backtest_config=BacktestConfig(initial_cash=initial_cash),
        )
    result = backtest_xgboost_oos_run(
        history,
        symbol=symbol,
        oos=oos,
        threshold=threshold,
        backtest_config=config,
    )
    benchmark_window = _oos_replay_window(history, oos.probabilities)
    benchmark_final = _buy_and_hold_return(benchmark_window, initial_cash)
    strategy_return = result.final_cash / initial_cash - 1.0
    benchmark_return = benchmark_final / initial_cash - 1.0
    return {
        "symbol": symbol,
        "period": period,
        "rows": int(len(history)),
        "quality_valid": bool(quality.valid) if quality is not None else None,
        "quality_report": quality.__dict__ if quality is not None else None,
        "oos_folds": oos.folds,
        "oos_rows": oos.test_rows,
        "oos_start": oos.probabilities.index.min().isoformat(),
        "oos_end": oos.probabilities.index.max().isoformat(),
        "benchmark_start": benchmark_window.index.min().isoformat(),
        "benchmark_end": benchmark_window.index.max().isoformat(),
        "threshold": threshold,
        "initial_cash": initial_cash,
        "final_cash": result.final_cash,
        "strategy_return": strategy_return,
        "benchmark_return": benchmark_return,
        "excess_return_vs_buy_hold": strategy_return - benchmark_return,
        "max_drawdown": _max_drawdown(result.equity),
        "trades": result.trades,
        "total_commission": result.total_commission,
        "total_slippage": result.total_slippage,
        "final_position": result.final_position,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default="5y")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--commission-rate", type=float, default=0.001)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--oos-artifact-dir", default=None)
    parser.add_argument("--output", default="artifacts/xgboost-oos-economic-report/report.json")
    args = parser.parse_args()
    reports = [
        run_symbol(
            s,
            period=args.period,
            horizon=args.horizon,
            train_size=args.train_size,
            test_size=args.test_size,
            step=args.step,
            threshold=args.threshold,
            initial_cash=args.initial_cash,
            commission_rate=args.commission_rate,
            slippage_bps=args.slippage_bps,
            oos_artifact_dir=args.oos_artifact_dir,
        )
        for s in CI_SYMBOLS
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2, default=str), encoding="utf-8")
    print(json.dumps(reports, indent=2, default=str))


if __name__ == "__main__":
    main()
