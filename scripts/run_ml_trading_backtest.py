from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.evaluation import trading_metrics
from app.services.market_replay import MarketReplay
from app.services.ml_trading import predictions_to_long_only_signals, purged_walk_forward_predictions
from app.services.openbb_market_data import OpenBBMarketDataProvider

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
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


def run_symbol(provider: OpenBBMarketDataProvider, symbol: str) -> dict:
    frame, quality = provider.historical_with_quality(symbol, start=START, end=END, interval="1d")
    prediction_run = purged_walk_forward_predictions(frame.rename(columns=str.title))
    ml_signals = predictions_to_long_only_signals(prediction_run.predictions)
    eval_frame = frame.loc[prediction_run.predictions.index[0]:].copy()

    ml_result = _run_backtest(eval_frame, ml_signals)
    ema_result = _run_backtest(eval_frame, ema_cross_signal(eval_frame))

    buy_hold = pd.Series(
        CONFIG.initial_cash * eval_frame["close"] / float(eval_frame["close"].iloc[0]),
        index=eval_frame.index,
        name="buy_hold_equity",
    )

    return {
        "symbol": symbol,
        "rows": quality.rows,
        "evaluation_start": eval_frame.index[0].isoformat(),
        "evaluation_end": eval_frame.index[-1].isoformat(),
        "ml_prediction_folds": prediction_run.folds,
        "ml_prediction_rows": prediction_run.test_rows,
        "ml": {
            **trading_metrics(ml_result.equity),
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
    provider = OpenBBMarketDataProvider()
    reports = [run_symbol(provider, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/ml-trading-backtest-report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
