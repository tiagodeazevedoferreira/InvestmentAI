from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from .order_manager import OrderIntent


class DemoBrokerError(RuntimeError):
    """Raised when the MT5 demo adapter cannot safely complete an operation."""


class MT5Gateway(Protocol):
    def account_info(self) -> Any: ...
    def symbol_info(self, symbol: str) -> Any: ...
    def positions_get(self) -> Any: ...
    def orders_get(self) -> Any: ...
    def history_deals_get(self, date_from: datetime, date_to: datetime) -> Any: ...
    def order_send(self, request: dict[str, Any]) -> Any: ...
    def order_check(self, request: dict[str, Any]) -> Any: ...
    def initialize(self) -> bool: ...
    def shutdown(self) -> None: ...
    def last_error(self) -> Any: ...


@dataclass(frozen=True)
class DemoAccountSnapshot:
    login: str
    server: str
    balance: float
    equity: float
    currency: str
    trade_allowed: bool


class MetaTrader5DemoGateway:
    """Thin, lazy MT5 gateway. It never connects to a live account."""

    def __init__(self, *, login: int | None = None, server: str | None = None, password: str | None = None) -> None:
        self.login = login
        self.server = server
        self.password = password
        self._mt5: Any | None = None

    def _module(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5  # type: ignore
            except ImportError as exc:
                raise DemoBrokerError("MetaTrader5 package is not installed") from exc
            self._mt5 = mt5
        return self._mt5

    def initialize(self) -> bool:
        mt5 = self._module()
        kwargs: dict[str, Any] = {}
        if self.login is not None:
            kwargs["login"] = self.login
        if self.server:
            kwargs["server"] = self.server
        if self.password:
            kwargs["password"] = self.password
        ok = bool(mt5.initialize(**kwargs))
        if not ok:
            raise DemoBrokerError(f"MT5 initialize failed: {mt5.last_error()}")
        return True

    def shutdown(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()

    def account_info(self) -> Any:
        return self._module().account_info()

    def symbol_info(self, symbol: str) -> Any:
        return self._module().symbol_info(symbol)

    def positions_get(self) -> Any:
        return self._module().positions_get()

    def orders_get(self) -> Any:
        return self._module().orders_get()

    def history_deals_get(self, date_from: datetime, date_to: datetime) -> Any:
        return self._module().history_deals_get(date_from, date_to)

    def order_check(self, request: dict[str, Any]) -> Any:
        return self._module().order_check(request)

    def order_send(self, request: dict[str, Any]) -> Any:
        return self._module().order_send(request)

    def last_error(self) -> Any:
        return self._module().last_error()


class MT5DemoBroker:
    """BrokerAdapter-compatible demo-only execution and reconciliation facade."""

    environment = "demo"
    name = "doto-mt5-demo"

    def __init__(self, gateway: MT5Gateway, *, require_demo_server: bool = True) -> None:
        self.gateway = gateway
        self.require_demo_server = require_demo_server

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _ensure_demo_account(self) -> Any:
        account = self.gateway.account_info()
        if account is None:
            raise DemoBrokerError("MT5 account_info returned no account")
        server = str(self._value(account, "server", ""))
        trade_mode = self._value(account, "trade_mode")
        if self.require_demo_server and "demo" not in server.lower():
            raise DemoBrokerError("Refusing non-demo MT5 server")
        if trade_mode is not None and str(trade_mode).lower() in {"real", "live"}:
            raise DemoBrokerError("Refusing MT5 real/live trade mode")
        return account

    def account(self) -> DemoAccountSnapshot:
        account = self._ensure_demo_account()
        return DemoAccountSnapshot(
            login=str(self._value(account, "login", "")),
            server=str(self._value(account, "server", "")),
            balance=float(self._value(account, "balance", 0.0)),
            equity=float(self._value(account, "equity", 0.0)),
            currency=str(self._value(account, "currency", "")),
            trade_allowed=bool(self._value(account, "trade_allowed", False)),
        )

    def positions(self) -> list[dict[str, Any]]:
        self._ensure_demo_account()
        return [self._position(row) for row in (self.gateway.positions_get() or [])]

    def open_orders(self) -> list[dict[str, Any]]:
        self._ensure_demo_account()
        return [self._order(row) for row in (self.gateway.orders_get() or [])]

    def executions(self, date_from: datetime, date_to: datetime) -> list[dict[str, Any]]:
        self._ensure_demo_account()
        return [self._deal(row) for row in (self.gateway.history_deals_get(date_from, date_to) or [])]

    def reconciliation_snapshot(self, date_from: datetime, date_to: datetime) -> dict[str, Any]:
        """Return the normalized external state consumed by OperationalReconciler."""
        account = self.account()
        return {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "cash": account.balance,
            "equity": account.equity,
            "currency": account.currency,
            "positions": {
                item["symbol"]: {"quantity": item["quantity"], "side": item["side"]}
                for item in self.positions()
            },
            "open_orders": self.open_orders(),
            "executions": self.executions(date_from, date_to),
        }

    def submit(self, intent: OrderIntent) -> dict[str, Any]:
        account = self._ensure_demo_account()
        if not bool(self._value(account, "trade_allowed", False)):
            raise DemoBrokerError("MT5 demo account does not allow trading")
        if intent.quantity <= 0:
            raise ValueError("quantity must be positive")
        if intent.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        symbol = intent.symbol.upper()
        info = self.gateway.symbol_info(symbol)
        if info is None:
            raise DemoBrokerError(f"Unknown MT5 symbol: {symbol}")
        mt5 = getattr(self.gateway, "_mt5", None)
        if mt5 is None:
            buy_type = getattr(self.gateway, "ORDER_TYPE_BUY", 0)
            sell_type = getattr(self.gateway, "ORDER_TYPE_SELL", 1)
            action = getattr(self.gateway, "TRADE_ACTION_DEAL", 1)
            filling = getattr(self.gateway, "ORDER_FILLING_IOC", 1)
        else:
            buy_type = mt5.ORDER_TYPE_BUY
            sell_type = mt5.ORDER_TYPE_SELL
            action = mt5.TRADE_ACTION_DEAL
            filling = mt5.ORDER_FILLING_IOC
        tick = self._value(info, "last", None) or self._value(info, "ask" if intent.side == "BUY" else "bid", None)
        if tick is None:
            raise DemoBrokerError(f"No executable price for {symbol}")
        request = {"action": action, "symbol": symbol, "volume": float(intent.quantity), "type": buy_type if intent.side == "BUY" else sell_type, "price": float(intent.limit_price if intent.limit_price is not None else tick), "deviation": 20, "type_filling": filling, "comment": "InvestmentAI demo"}
        check = self.gateway.order_check(request)
        if check is None:
            raise DemoBrokerError("MT5 order_check returned no result")
        check_retcode = self._value(check, "retcode", None)
        if check_retcode not in (None, 0, getattr(mt5, "TRADE_RETCODE_DONE", 10009) if mt5 else 10009):
            raise DemoBrokerError(f"MT5 order_check rejected request: {check_retcode}")
        result = self.gateway.order_send(request)
        if result is None:
            raise DemoBrokerError("MT5 order_send returned no result")
        retcode = self._value(result, "retcode", None)
        done = getattr(mt5, "TRADE_RETCODE_DONE", 10009) if mt5 else 10009
        if retcode != done:
            raise DemoBrokerError(f"MT5 order_send rejected request: {retcode}")
        return {"order_id": str(self._value(result, "order", "")), "deal_id": str(self._value(result, "deal", "")), "status": "accepted", "environment": self.environment, "symbol": symbol, "side": intent.side, "quantity": intent.quantity, "price": float(self._value(result, "price", request["price"])), "timestamp": datetime.now(timezone.utc).isoformat()}

    def cancel(self, order_id: str) -> dict[str, Any]:
        raise DemoBrokerError("Pending-order cancellation is not implemented until broker order semantics are validated")

    def _position(self, row: Any) -> dict[str, Any]:
        return {"position_id": str(self._value(row, "ticket", "")), "symbol": str(self._value(row, "symbol", "")).upper(), "quantity": float(self._value(row, "volume", 0.0)), "side": "BUY" if self._value(row, "type", 0) == 0 else "SELL", "price_open": float(self._value(row, "price_open", 0.0))}

    def _order(self, row: Any) -> dict[str, Any]:
        return {"order_id": str(self._value(row, "ticket", "")), "symbol": str(self._value(row, "symbol", "")).upper(), "quantity": float(self._value(row, "volume_current", self._value(row, "volume_initial", 0.0))), "type": self._value(row, "type", None), "status": self._value(row, "state", None)}

    def _deal(self, row: Any) -> dict[str, Any]:
        return {"execution_id": str(self._value(row, "ticket", "")), "order_id": str(self._value(row, "order", "")), "symbol": str(self._value(row, "symbol", "")).upper(), "quantity": float(self._value(row, "volume", 0.0)), "price": float(self._value(row, "price", 0.0)), "time": self._value(row, "time", None)}
