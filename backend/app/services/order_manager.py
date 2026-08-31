from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from .execution import can_execute_live


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: str
    quantity: int
    limit_price: float | None = None


class ExecutionBlocked(RuntimeError):
    pass


class SimulatedBroker:
    name = "simulated"
    environment = "simulation"

    def submit(self, intent: OrderIntent) -> dict:
        if intent.quantity <= 0:
            raise ValueError("quantity must be positive")
        if intent.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        return {"order_id": str(uuid4()), "status": "accepted", "environment": self.environment,
                "symbol": intent.symbol.upper(), "side": intent.side, "quantity": intent.quantity,
                "limit_price": intent.limit_price, "timestamp": datetime.now(timezone.utc).isoformat()}


class OrderManager:
    def __init__(self, broker=None):
        self.broker = broker or SimulatedBroker()

    def submit(self, intent: OrderIntent, environment: str = "simulation") -> dict:
        environment = environment.lower()
        if environment == "live":
            allowed, reason = can_execute_live()
            if not allowed:
                raise ExecutionBlocked(reason)
        if environment != getattr(self.broker, "environment", "simulation"):
            raise ExecutionBlocked(f"Broker environment mismatch: requested {environment}")
        return self.broker.submit(intent)
