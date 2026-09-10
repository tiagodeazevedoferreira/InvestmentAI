from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .order_manager import OrderIntent


class DemoOrderPreflightError(ValueError):
    """Raised when a DEMO order intent fails deterministic preflight checks."""


@dataclass(frozen=True)
class DemoOrderPreflight:
    """Validate a first controlled DEMO order without contacting MT5.

    This layer is intentionally broker-independent and side-effect free. It
    validates the intent and explicit execution policy before the broker's
    market-data and order_check gates are reached.
    """

    max_volume: float = 0.01
    allowed_symbols: frozenset[str] | None = None

    def __post_init__(self) -> None:
        if self.max_volume <= 0:
            raise ValueError("max_volume must be positive")
        if self.allowed_symbols is not None:
            normalized = frozenset(symbol.strip().upper() for symbol in self.allowed_symbols if symbol.strip())
            if not normalized:
                raise ValueError("allowed_symbols must contain at least one non-empty symbol")
            object.__setattr__(self, "allowed_symbols", normalized)

    def validate(self, intent: OrderIntent, *, environment: str = "demo") -> OrderIntent:
        if environment.strip().lower() != "demo":
            raise DemoOrderPreflightError("DEMO order preflight requires environment=demo")

        symbol = intent.symbol.strip().upper()
        if not symbol:
            raise DemoOrderPreflightError("symbol cannot be empty")
        if self.allowed_symbols is not None and symbol not in self.allowed_symbols:
            raise DemoOrderPreflightError(f"symbol is not approved for controlled DEMO execution: {symbol}")

        side = intent.side.strip().upper()
        if side not in {"BUY", "SELL"}:
            raise DemoOrderPreflightError("side must be BUY or SELL")

        quantity = float(intent.quantity)
        if quantity <= 0:
            raise DemoOrderPreflightError("quantity must be positive")
        if quantity > self.max_volume:
            raise DemoOrderPreflightError(
                f"requested volume exceeds DEMO preflight limit: {quantity} > {self.max_volume}"
            )

        if intent.limit_price is not None:
            raise DemoOrderPreflightError(
                "limit_price is unsupported until MT5 pending-order semantics are implemented"
            )

        return OrderIntent(symbol=symbol, side=side, quantity=quantity, limit_price=None)

    def validate_state(self, state: Mapping[str, object]) -> None:
        """Validate the minimum internal state shape required for reconciliation."""
        for key in ("cash", "positions", "open_orders", "executions"):
            if key not in state:
                raise DemoOrderPreflightError(f"internal state is missing required field: {key}")
        if not isinstance(state["positions"], Mapping):
            raise DemoOrderPreflightError("positions must be a mapping")
        if not isinstance(state["open_orders"], list):
            raise DemoOrderPreflightError("open_orders must be a list")
        if not isinstance(state["executions"], list):
            raise DemoOrderPreflightError("executions must be a list")
