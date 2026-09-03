from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .paper_execution import PaperAccount, PaperExecutionError
from .technical import indicators, rsi_signal


@dataclass(frozen=True)
class AutomationDecision:
    symbol: str
    action: str
    quantity: int
    reference_price: float
    risk_allowed: bool
    reason: str
    timestamp: str


def evaluate_paper_signal(
    account: PaperAccount,
    symbol: str,
    market_data: pd.DataFrame,
    *,
    max_order_notional: float = 10_000.0,
    target_allocation: float = 0.05,
    execute: bool = True,
) -> dict[str, Any]:
    """Run a deterministic technical signal through risk, sizing and paper execution.

    This is deliberately a conservative first automation policy: RSI<30 buys and
    RSI>70 sells, no shorting, and BUY sizing is capped by both target allocation
    and the configured order-notional limit. HOLD never creates an order.
    """
    if max_order_notional <= 0 or not 0 < target_allocation <= 1:
        raise ValueError("invalid automation risk parameters")
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("symbol is required")

    frame = indicators(market_data)
    if frame.empty:
        raise ValueError("No market data available")
    row = frame.iloc[-1]
    price = float(row["Close"])
    action = rsi_signal(row)
    rsi = row.get("RSI14")
    rsi_text = "unavailable" if pd.isna(rsi) else f"{float(rsi):.2f}"

    reason = f"RSI14={rsi_text}; policy=RSI<30 BUY / RSI>70 SELL"
    quantity = 0
    risk_allowed = True

    if action == "BUY":
        budget = min(account.equity * target_allocation, max_order_notional)
        quantity = int(budget // price)
        if quantity <= 0:
            risk_allowed = False
            reason += "; risk gate rejected: calculated quantity is zero"
    elif action == "SELL":
        position = account.positions.get(symbol)
        quantity = position.quantity if position else 0
        if quantity == 0:
            risk_allowed = False
            reason += "; risk gate rejected: no position to sell"

    decision = AutomationDecision(
        symbol=symbol,
        action=action,
        quantity=quantity,
        reference_price=price,
        risk_allowed=risk_allowed,
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    result: dict[str, Any] = {
        "decision": decision.__dict__,
        "executed": False,
        "order": None,
    }
    if execute and action in {"BUY", "SELL"} and risk_allowed and quantity > 0:
        try:
            order = account.submit_order(
                symbol=symbol,
                side=action,
                quantity=quantity,
                reference_price=price,
                reason=reason,
            )
        except (ValueError, PaperExecutionError) as exc:
            result["error"] = str(exc)
        else:
            result["executed"] = True
            result["order"] = order
    return result
