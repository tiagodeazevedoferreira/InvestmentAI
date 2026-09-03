"""Provider-backed orchestration for paper trading decisions.

The orchestrator intentionally keeps market-data providers and execution
separate. It is safe-by-default: only the paper execution path is exposed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Protocol

import pandas as pd

from app.services.order_manager import OrderIntent, OrderManager


class MarketDataProvider(Protocol):
    def history(self, symbol: str, period: str = "6mo") -> pd.DataFrame: ...


@dataclass(frozen=True)
class AutoDecision:
    symbol: str
    action: str
    quantity: int
    price: float
    rsi: float
    bar_timestamp: str
    signal_id: str
    reason: str


def _timestamp(df: pd.DataFrame) -> str:
    if df.empty:
        raise ValueError("market data is empty")
    value = df.index[-1]
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def decide(df: pd.DataFrame, symbol: str, target_weight: float = 0.10) -> AutoDecision:
    if "Close" not in df.columns:
        raise ValueError("market data must contain Close")
    close = pd.to_numeric(df["Close"], errors="coerce").dropna()
    if len(close) < 20:
        raise ValueError("at least 20 valid closes are required")
    price = float(close.iloc[-1])
    rsi = float(_rsi(close).iloc[-1])
    bar_timestamp = _timestamp(df.loc[close.index])
    if rsi < 30:
        action = "BUY"
        reason = "RSI below oversold threshold"
    elif rsi > 70:
        action = "SELL"
        reason = "RSI above overbought threshold"
    else:
        action = "HOLD"
        reason = "RSI inside neutral band"
    quantity = max(1, int(target_weight * 100)) if action == "BUY" else 1
    signal_id = sha256(f"{symbol}|{bar_timestamp}|{action}".encode()).hexdigest()[:24]
    return AutoDecision(symbol, action, quantity, price, rsi, bar_timestamp, signal_id, reason)


def execute_once(provider: MarketDataProvider, order_manager: OrderManager, symbol: str,
                 target_weight: float = 0.10) -> AutoDecision:
    decision = decide(provider.history(symbol), symbol, target_weight)
    if decision.action != "HOLD":
        intent = OrderIntent(
            symbol=decision.symbol,
            side=decision.action,
            quantity=decision.quantity,
            order_type="MARKET",
            limit_price=None,
            client_order_id=f"paper-{decision.signal_id}",
        )
        order_manager.submit(intent, market_price=decision.price)
    return decision
