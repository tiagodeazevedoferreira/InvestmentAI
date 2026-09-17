from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.ci_market_data import CI_SYMBOLS, MarketDataSource, load_market_history
from app.services.evaluation import trading_metrics
from app.services.market_replay import MarketReplay
from app.services.xgboost_oos import run_xgboost_oos_backtest

SYMBOLS = CI_SYMBOLS
START = "2021-01-01"
END = "2026-09-01"
CONFIG = BacktestConfig(initial_cash=100_000.0, commission_rate=0.001, slippage_bps=5.0)


def ema_cross_signal(frame: pd.DataFrame) -> pd.Series:
    close = frame["close"].astype(float)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    previous_fast = ema9.shift(1)
    previous_slow = ema21.shift(1)
    signals = pd.Series(0, index=frame.index, dtype=int)
    signals[(ema9 > ema21) & (previous_fast <= previous_slow)] = 1
    signals[(ema9 < ema21) & (previous_fast >= previous_slow)] = -1
    return signals


def _run_backtest(frame: pd.DataFrame, signals: pd.Series):
    replay = MarketReplay("ML", frame)
    signal_iter = iter(signals.reindex(frame.index, fill_value=0).tolist())

    def signal_fn(_bar):
        return next(signal_iter)

    return Backtester(CONFIG).run(replay, signal_fn)


def run_symbol(source: MarketDataSource, symbol: str) -> dict:
    frame, quality = load_market_history(symbol, source=source, start=START, end=END, interval="1d")
    assert quality is not None
    frame = frame.rename(
        columns={column: str(column).lower() for column in frame.columns}
    )

    xgboost_oos, ml_result = run_xgboost_oos_backtest(
        frame,
        symbol=symbol,
        backtest_config=CONFIG,
    )

    eval_frame = frame.loc[ml_result.equity.index[0] : ml_result.equity.index[-1]].copy()
    ema_result = _run_backtest(eval_frame, ema_cross_signal(eval_frame))

    buy_hold = pd.Series(
        CONFIG.initial_cash * eval_frame["close"] / float(eval_frame["close"].iloc[0]),
        index=eval_frame.index,
        name="buy_hold_equity",
    )

    return {
        "symbol": symbol,
        "source": source,
        "rows": quality.rows,
        "evaluation_start": ml_result.equity.index[0].isoformat(),
        "evaluation_end": ml_result.equity.index[-1].isoformat(),
        "ml_prediction_folds": xgboost_oos.folds,
        "ml_prediction_rows": xgboost_oos.test_rows,
        "ml": {
            **trading_metrics(ml_result.equity),
            "model": "xgboost",
            "trades": ml_result.trades,
            "final_cash": ml_result.final_cash,
            "total_commission": ml_result.total_commission,
            "total_slippage": ml_result.total_slippage,
        },
        "ema_9_21": {
            **trading_metrics(ema_result.equity),
            "trades": ema_result.trades,
            "final_cash": ema_result.final_cash,
            "total_commission": ema_result.total_commission,
            "total_slippage": ema_result.total_slippage,
        },
        "buy_and_hold": trading_metrics(buy_hold),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run causal ML trading backtests.")
    parser.add_argument(
        "--source",
        choices=("fixture", "provider"),
        default="fixture",
        help="Data source. The deterministic fixture is the CI default; provider is an explicit external-data mode.",
    )
    args = parser.parse_args()
    source: MarketDataSource = args.source

    reports = [run_symbol(source, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/ml-trading-backtest-report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
