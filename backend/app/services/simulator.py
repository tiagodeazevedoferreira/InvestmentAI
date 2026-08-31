from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


@dataclass
class Position:
    quantity: float = 0.0
    cash: float = 0.0


class MarketSimulator:
    """Deterministic single/multi-asset simulator for paper and RL experiments."""
    def __init__(self, initial_cash: float = 10000.0, commission_bps: float = 5.0, slippage_bps: float = 5.0):
        if initial_cash <= 0 or commission_bps < 0 or slippage_bps < 0:
            raise ValueError("invalid simulator parameters")
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps
        self.positions: dict[str, float] = {}

    def reset(self):
        self.cash = self.initial_cash
        self.positions.clear()

    def step(self, prices: dict[str, float], target_weights: dict[str, float]) -> dict:
        if not prices:
            raise ValueError("prices cannot be empty")
        if abs(sum(target_weights.values())) > 1.000001:
            raise ValueError("target weights cannot exceed 100% gross exposure")
        equity = self.cash + sum(self.positions.get(s, 0.0) * p for s, p in prices.items())
        turnover = 0.0
        for symbol, price in prices.items():
            target_value = equity * float(target_weights.get(symbol, 0.0))
            target_qty = target_value / price if price > 0 else 0.0
            delta = target_qty - self.positions.get(symbol, 0.0)
            if delta:
                execution_price = price * (1 + self.slippage_bps / 10000 * (1 if delta > 0 else -1))
                notional = delta * execution_price
                fee = abs(notional) * self.commission_bps / 10000
                self.cash -= notional + fee
                self.positions[symbol] = target_qty
                turnover += abs(notional)
        new_equity = self.cash + sum(self.positions.get(s, 0.0) * p for s, p in prices.items())
        return {"equity": new_equity, "cash": self.cash, "turnover": turnover, "positions": dict(self.positions)}
