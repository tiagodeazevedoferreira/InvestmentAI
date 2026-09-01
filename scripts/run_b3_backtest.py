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


def _ema(previous: float | None, price: float, span: int) -> float:
    alpha = 2.0 / (span + 1.0)
    return price if previous is None else alpha * price + (1.0 - alpha) * previous


def ema_cross_signal(frame: pd.DataFrame) -> pd.Series:
    """Return EMA 9/21 crossover signals using only data available at each bar."""
    close = frame["close"].astype(float)
    fast: float | None = None
    slow: float | None = None
    previous_fast: float | None = None
    previous_slow: float | None = None
    signals: list[int] = []

    for price in close:
        fast = _ema(fast, float(price), 9)
        slow = _ema(slow, float(price), 21)
        signal = 0
        if previous_fast is not None and previous_slow is not None:
            if fast > slow and previous_fast <= previous_slow:
                signal = 1
            elif fast < slow and previous_fast >= previous_slow:
                signal = -1
        signals.append(signal)
        previous_fast, previous_slow = fast, slow

    return pd.Series(signals, index=frame.index, dtype=int)


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
        "start": frame.index[0].isoformat(),
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
