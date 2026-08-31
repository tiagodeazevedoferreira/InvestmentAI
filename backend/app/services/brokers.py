from __future__ import annotations
from .order_manager import SimulatedBroker, OrderIntent


class DemoBroker(SimulatedBroker):
    """Broker contract for a real sandbox API. No live endpoint is ever used."""
    name = "demo-sandbox"
    environment = "demo"


class BrokerAdapter:
    """Minimal contract to isolate broker SDKs from domain logic."""
    environment = "unknown"

    def submit(self, intent: OrderIntent) -> dict:
        raise NotImplementedError

    def cancel(self, order_id: str) -> dict:
        raise NotImplementedError

    def positions(self) -> list[dict]:
        raise NotImplementedError
