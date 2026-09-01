from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class PaperBroker:
    """Deterministic, in-process paper broker. Never routes to a live venue."""
    name: str = "investmentai-paper"
    environment: str = "paper"
    cash: float = 10000.0
    positions: dict[str, int] = field(default_factory=dict)
    orders: list[dict] = field(default_factory=list)

    def submit(self, symbol: str, side: str, quantity: int, price: float) -> dict:
        symbol, side = symbol.upper(), side.upper()
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        notional = quantity * price
        if side == "BUY":
            if notional > self.cash:
                raise ValueError("insufficient paper cash")
            self.cash -= notional
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        elif side == "SELL":
            if quantity > self.positions.get(symbol, 0):
                raise ValueError("insufficient paper position")
            self.positions[symbol] -= quantity
            self.cash += notional
        else:
            raise ValueError("side must be BUY or SELL")
        order = {"order_id": str(uuid4()), "symbol": symbol, "side": side, "quantity": quantity,
                 "price": price, "notional": notional, "status": "filled",
                 "environment": self.environment, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.orders.append(order)
        return order

    def snapshot(self) -> dict:
        return {"cash": self.cash, "positions": dict(self.positions), "orders": list(self.orders), "environment": self.environment}
