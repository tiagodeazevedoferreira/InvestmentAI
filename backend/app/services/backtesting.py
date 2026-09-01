from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import pandas as pd

from app.services.market_replay import MarketBar, MarketReplay


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 100_000.0
    commission_rate: float = 0.0
    slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.commission_rate < 0:
            raise ValueError("commission_rate cannot be negative")
        if self.slippage_bps < 0:
            raise ValueError("slippage_bps cannot be negative")


@dataclass(frozen=True)
class BacktestResult:
    equity: pd.Series
    trades: int
    final_cash: float
    final_position: float
    total_commission: float
    total_slippage: float


SignalFn = Callable[[MarketBar], int]


class Backtester:
    """Long-only, deterministic close-to-close backtester.

    A signal generated from bar t is executed at bar t+1 open. This prevents the
    strategy from using the current close to trade at that same close and avoids
    look-ahead bias. Signals are -1 (exit), 0 (hold), or 1 (enter).
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()

    def run(self, replay: MarketReplay, signal_fn: SignalFn) -> BacktestResult:
        bars = iter(replay)
        try:
            current = next(bars)
        except StopIteration as exc:
            raise ValueError("market replay is empty") from exc

        cash = self.config.initial_cash
        position = 0.0
        commission_total = 0.0
        slippage_total = 0.0
        trades = 0
        equity_values: list[float] = []
        equity_index: list[pd.Timestamp] = []
        pending_signal = 0

        while True:
            # Execute the previous bar's signal at the current bar's open.
            if pending_signal != 0:
                target = 1 if pending_signal > 0 else 0
                if target == 1 and position == 0:
                    execution_price = current.open * (1 + self.config.slippage_bps / 10_000)
                    quantity = cash / (execution_price * (1 + self.config.commission_rate))
                    gross = quantity * execution_price
                    commission = gross * self.config.commission_rate
                    cash -= gross + commission
                    position = quantity
                    commission_total += commission
                    slippage_total += quantity * abs(execution_price - current.open)
                    trades += 1
                elif target == 0 and position > 0:
                    execution_price = current.open * (1 - self.config.slippage_bps / 10_000)
                    gross = position * execution_price
                    commission = gross * self.config.commission_rate
                    cash += gross - commission
                    slippage_total += position * abs(execution_price - current.open)
                    commission_total += commission
                    position = 0.0
                    trades += 1

            equity = cash + position * current.close
            equity_values.append(equity)
            equity_index.append(current.timestamp)

            next_signal = int(signal_fn(current))
            if next_signal not in (-1, 0, 1):
                raise ValueError("signal_fn must return -1, 0, or 1")
            pending_signal = next_signal

            try:
                current = next(bars)
            except StopIteration:
                break

        # Liquidate at the final close so final equity is economically realizable.
        if position > 0:
            execution_price = current.close * (1 - self.config.slippage_bps / 10_000)
            gross = position * execution_price
            commission = gross * self.config.commission_rate
            cash += gross - commission
            slippage_total += position * abs(execution_price - current.close)
            commission_total += commission
            position = 0.0
            trades += 1
            equity_values[-1] = cash

        equity = pd.Series(equity_values, index=pd.DatetimeIndex(equity_index), name="equity")
        return BacktestResult(
            equity=equity,
            trades=trades,
            final_cash=float(cash),
            final_position=float(position),
            total_commission=float(commission_total),
            total_slippage=float(slippage_total),
        )
