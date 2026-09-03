from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


class PaperExecutionError(RuntimeError):
    """Raised when a paper order cannot be executed safely."""


@dataclass
class PaperPosition:
    symbol: str
    quantity: int = 0
    average_price: float = 0.0
    market_price: float = 0.0

    @property
    def market_value(self) -> float:
        return round(self.quantity * self.market_price, 8)

    @property
    def unrealized_pnl(self) -> float:
        return round((self.market_price - self.average_price) * self.quantity, 8)


@dataclass
class PaperAccount:
    """Deterministic paper account with cash, fills and portfolio accounting."""

    initial_cash: float = 100_000.0
    fee_bps: float = 5.0
    slippage_bps: float = 5.0
    cash: float | None = None
    positions: dict[str, PaperPosition] = field(default_factory=dict)
    orders: list[dict] = field(default_factory=list)
    executions: list[dict] = field(default_factory=list)
    realized_pnl: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ValueError("fee_bps and slippage_bps cannot be negative")
        if self.cash is None:
            self.cash = float(self.initial_cash)

    @staticmethod
    def _normalize(symbol: str, side: str) -> tuple[str, str]:
        symbol = symbol.strip().upper()
        side = side.strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        return symbol, side

    def _existing_client_order(self, client_order_id: str | None) -> dict | None:
        if not client_order_id:
            return None
        for order in self.orders:
            if order.get("client_order_id") == client_order_id:
                return dict(order)
        return None

    def submit_order(
        self, symbol: str, side: str, quantity: int, reference_price: float,
        order_type: str = "MARKET", limit_price: float | None = None,
        reason: str | None = None, client_order_id: str | None = None,
    ) -> dict:
        symbol, side = self._normalize(symbol, side)
        existing = self._existing_client_order(client_order_id)
        if existing is not None:
            return existing
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if reference_price <= 0:
            raise ValueError("reference_price must be positive")
        order_type = order_type.strip().upper()
        if order_type not in {"MARKET", "LIMIT"}:
            raise ValueError("order_type must be MARKET or LIMIT")
        if order_type == "LIMIT" and (limit_price is None or limit_price <= 0):
            raise ValueError("limit_price must be positive for LIMIT orders")

        order_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if order_type == "LIMIT":
            executable = reference_price <= limit_price if side == "BUY" else reference_price >= limit_price
            if not executable:
                order = {
                    "order_id": order_id, "client_order_id": client_order_id, "symbol": symbol, "side": side,
                    "quantity": quantity, "order_type": order_type,
                    "limit_price": float(limit_price), "status": "open",
                    "environment": "paper", "reason": reason, "timestamp": now,
                }
                self.orders.append(order)
                return dict(order)

        fill_price = self._apply_slippage(reference_price, side)
        fee = round(quantity * fill_price * self.fee_bps / 10_000.0, 8)
        notional = round(quantity * fill_price, 8)
        self._apply_fill(symbol, side, quantity, fill_price, fee, notional)

        order = {
            "order_id": order_id, "client_order_id": client_order_id, "symbol": symbol, "side": side, "quantity": quantity,
            "order_type": order_type, "reference_price": float(reference_price),
            "limit_price": float(limit_price) if limit_price is not None else None,
            "status": "filled", "environment": "paper", "reason": reason, "timestamp": now,
        }
        execution = {
            "execution_id": str(uuid4()), "order_id": order_id, "symbol": symbol,
            "side": side, "quantity": quantity, "fill_price": fill_price,
            "notional": notional, "fee": fee, "slippage_bps": self.slippage_bps,
            "timestamp": now,
        }
        self.orders.append(order)
        self.executions.append(execution)
        return {**order, "execution": execution}

    def mark_to_market(self, prices: dict[str, float]) -> dict:
        normalized = {}
        for symbol, price in prices.items():
            symbol = symbol.strip().upper()
            if price <= 0:
                raise ValueError(f"invalid market price for {symbol}")
            normalized[symbol] = float(price)
            if symbol in self.positions:
                self.positions[symbol].market_price = float(price)
        self._fill_crossed_limits(normalized)
        return self.snapshot()

    def _fill_crossed_limits(self, prices: dict[str, float]) -> None:
        for order in list(self.orders):
            if order.get("status") != "open" or order["symbol"] not in prices:
                continue
            price = prices[order["symbol"]]
            side = order["side"]
            limit = order["limit_price"]
            executable = price <= limit if side == "BUY" else price >= limit
            if not executable:
                continue
            fill_price = self._apply_slippage(price, side)
            fee = round(order["quantity"] * fill_price * self.fee_bps / 10_000.0, 8)
            notional = round(order["quantity"] * fill_price, 8)
            try:
                self._apply_fill(order["symbol"], side, order["quantity"], fill_price, fee, notional)
            except PaperExecutionError:
                continue
            order["status"] = "filled"
            execution = {
                "execution_id": str(uuid4()), "order_id": order["order_id"],
                "symbol": order["symbol"], "side": side, "quantity": order["quantity"],
                "fill_price": fill_price, "notional": notional, "fee": fee,
                "slippage_bps": self.slippage_bps,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.executions.append(execution)

    def _apply_fill(self, symbol: str, side: str, quantity: int, price: float, fee: float, notional: float) -> None:
        if side == "BUY":
            total_cost = notional + fee
            if total_cost > float(self.cash) + 1e-9:
                raise PaperExecutionError("insufficient paper cash")
            self.cash = round(float(self.cash) - total_cost, 8)
            self._buy(symbol, quantity, price)
            return
        position = self.positions.get(symbol)
        if position is None or quantity > position.quantity:
            raise PaperExecutionError("insufficient paper position")
        self.cash = round(float(self.cash) + notional - fee, 8)
        self._sell(symbol, quantity, price, fee)

    def cancel_open_orders(self) -> int:
        count = 0
        for order in self.orders:
            if order.get("status") == "open":
                order["status"] = "cancelled"
                count += 1
        return count

    def _apply_slippage(self, price: float, side: str) -> float:
        factor = self.slippage_bps / 10_000.0
        return round(price * (1.0 + factor if side == "BUY" else 1.0 - factor), 8)

    def _buy(self, symbol: str, quantity: int, price: float) -> None:
        position = self.positions.get(symbol)
        if position is None:
            self.positions[symbol] = PaperPosition(symbol, quantity, price, price)
            return
        total_quantity = position.quantity + quantity
        position.average_price = round(
            (position.quantity * position.average_price + quantity * price) / total_quantity, 8
        )
        position.quantity = total_quantity
        position.market_price = price

    def _sell(self, symbol: str, quantity: int, price: float, fee: float) -> None:
        position = self.positions[symbol]
        self.realized_pnl = round(
            self.realized_pnl + (price - position.average_price) * quantity - fee, 8
        )
        position.quantity -= quantity
        position.market_price = price
        if position.quantity == 0:
            del self.positions[symbol]

    @property
    def market_value(self) -> float:
        return round(sum(p.market_value for p in self.positions.values()), 8)

    @property
    def equity(self) -> float:
        return round(float(self.cash) + self.market_value, 8)

    @property
    def unrealized_pnl(self) -> float:
        return round(sum(p.unrealized_pnl for p in self.positions.values()), 8)

    def snapshot(self) -> dict:
        return {
            "environment": "paper", "initial_cash": round(self.initial_cash, 8),
            "fee_bps": self.fee_bps, "slippage_bps": self.slippage_bps,
            "cash": round(float(self.cash), 8), "market_value": self.market_value,
            "equity": self.equity, "realized_pnl": round(self.realized_pnl, 8),
            "unrealized_pnl": self.unrealized_pnl,
            "positions": {
                symbol: {
                    "symbol": p.symbol, "quantity": p.quantity,
                    "average_price": p.average_price, "market_price": p.market_price,
                    "market_value": p.market_value, "unrealized_pnl": p.unrealized_pnl,
                } for symbol, p in self.positions.items()
            },
            "open_orders": [o for o in self.orders if o.get("status") == "open"],
            "orders_count": len(self.orders), "executions_count": len(self.executions),
        }
