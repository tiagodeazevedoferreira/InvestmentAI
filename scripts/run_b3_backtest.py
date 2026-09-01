from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.evaluation import trading_metrics
from app.services.market_replay import MarketReplay
from app.services.openbb_market_data import OpenBBMarketDataProvider

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
START = "2021-01-01"
END = "2026-09-01"


def ema_cross_signal(frame: pd.DataFrame):
    close = frame["close"].astype(float)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    previous_fast = ema9.shift(1)
    previous_slow = ema21.shift(1)
    signals = pd.Series(0, index=frame.index, dtype=int)
    signals[(ema9 > ema21) & (previous_fast <= previous_slow)] = 1
    signals[(ema9 < ema21) & (previous_fast >= previous_slow)] = -1
    return signals


def run_symbol(provider: OpenBBMarketDataProvider, symbol: str) -> dict:
    frame, quality = provider.historical_with_quality(symbol, start=START, end=END, interval="1d")
    replay = MarketReplay(symbol, frame)
    signals = ema_cross_signal(frame)
    signal_iter = iter(signals.tolist())

    def signal_fn(_bar):
        return next(signal_iter)

    result = Backtester(
        BacktestConfig(initial_cash=100_000.0, commission_rate=0.001, slippage_bps=5.0)
    ).run(replay, signal_fn)

    buy_hold = pd.Series(
        100_000.0 * frame["close"] / float(frame["close"].iloc[0]),
        index=frame.index,
        name="buy_hold_equity",
    )
    strategy_metrics = trading_metrics(result.equity)
    benchmark_metrics = trading_metrics(buy_hold)
    return {
        "symbol": symbol,
        "rows": quality.rows,
        "start": quality.symbol and frame.index[0].isoformat(),
        "end": frame.index[-1].isoformat(),
        "strategy": {
            **strategy_metrics,
            "trades": result.trades,
            "final_cash": result.final_cash,
            "total_commission": result.total_commission,
            "total_slippage": result.total_slippage,
        },
        "buy_and_hold": benchmark_metrics,
    }


def main() -> None:
    provider = OpenBBMarketDataProvider()
    reports = [run_symbol(provider, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/b3-backtest-report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
