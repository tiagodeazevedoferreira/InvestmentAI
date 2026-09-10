from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .order_manager import OrderIntent


class MT5DemoExecutionError(RuntimeError):
    """Raised when a DEMO execution request cannot be safely completed."""


@dataclass(frozen=True)
class MT5DemoAccount:
    login: int
    server: str
    balance: float
    equity: float
    currency: str
    trade_allowed: bool
    trade_expert: bool


class MetaTrader5DemoBroker:
    """Fail-closed MT5 broker adapter restricted to an explicitly configured DEMO account."""

    environment = "demo"

    def __init__(self, *, terminal_path: str, expected_login: int, expected_server: str,
                 mt5_module: Any | None = None, execution_enabled: bool = False,
                 max_volume: float = 0.01) -> None:
        if not terminal_path:
            raise ValueError("terminal_path must not be empty")
        if expected_login <= 0:
            raise ValueError("expected_login must be positive")
        if not expected_server.strip():
            raise ValueError("expected_server must not be empty")
        if max_volume <= 0:
            raise ValueError("max_volume must be positive")
        self.terminal_path = terminal_path
        self.expected_login = expected_login
        self.expected_server = expected_server.strip()
        self._mt5 = mt5_module
        self.execution_enabled = execution_enabled
        self.max_volume = max_volume
        self._connected = False

    def _module(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5  # type: ignore
            except ImportError as exc:
                raise MT5DemoExecutionError("MetaTrader5 package is not installed") from exc
            self._mt5 = mt5
        return self._mt5

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)

    def connect(self) -> MT5DemoAccount:
        mt5 = self._module()
        try:
            ok = bool(mt5.initialize(path=self.terminal_path, timeout=60_000))
        except TypeError:
            ok = bool(mt5.initialize(path=self.terminal_path))
        if not ok:
            raise MT5DemoExecutionError(f"MT5 initialize failed: {mt5.last_error()}")
        self._connected = True
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None:
            self.close()
            raise MT5DemoExecutionError("MT5 account_info returned no account")
        if terminal is None or not bool(self._value(terminal, "connected", False)):
            self.close()
            raise MT5DemoExecutionError("MT5 terminal is not connected")
        login = int(self._value(account, "login", 0))
        server = str(self._value(account, "server", ""))
        if login != self.expected_login:
            self.close()
            raise MT5DemoExecutionError(f"DEMO account mismatch: {login}; expected {self.expected_login}")
        if server != self.expected_server:
            self.close()
            raise MT5DemoExecutionError(f"DEMO server mismatch: {server!r}; expected {self.expected_server!r}")
        return MT5DemoAccount(login, server, float(self._value(account, "balance", 0.0)),
                              float(self._value(account, "equity", 0.0)),
                              str(self._value(account, "currency", "")),
                              bool(self._value(account, "trade_allowed", False)),
                              bool(self._value(account, "trade_expert", False)))

    def submit(self, intent: OrderIntent) -> dict:
        if not self.execution_enabled:
            raise MT5DemoExecutionError("DEMO execution is disabled")
        if not self._connected:
            raise MT5DemoExecutionError("MT5 DEMO broker is not connected")
        if intent.quantity <= 0:
            raise ValueError("quantity must be positive")
        if float(intent.quantity) > self.max_volume:
            raise MT5DemoExecutionError(f"requested volume exceeds DEMO safety limit: {intent.quantity} > {self.max_volume}")
        if intent.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        mt5 = self._module()
        symbol = intent.symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol cannot be empty")
        if not mt5.symbol_select(symbol, True):
            raise MT5DemoExecutionError(f"cannot select MT5 symbol: {symbol}")
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if info is None or tick is None:
            raise MT5DemoExecutionError(f"MT5 market data unavailable for {symbol}")
        order_type = mt5.ORDER_TYPE_BUY if intent.side == "BUY" else mt5.ORDER_TYPE_SELL
        price = intent.limit_price
        if price is None:
            price = float(self._value(tick, "ask" if intent.side == "BUY" else "bid", 0.0))
        if price <= 0:
            raise MT5DemoExecutionError("invalid execution price")
        request = {"action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": float(intent.quantity),
                   "type": order_type, "price": price, "deviation": 20,
                   "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
                   "comment": "InvestmentAI-DEMO"}
        result = mt5.order_send(request)
        if result is None:
            raise MT5DemoExecutionError(f"MT5 order_send returned None: {mt5.last_error()}")
        retcode = int(self._value(result, "retcode", -1))
        return {"accepted": retcode in {getattr(mt5, "TRADE_RETCODE_DONE", 10009), getattr(mt5, "TRADE_RETCODE_PLACED", 10008)},
                "retcode": retcode, "order": self._value(result, "order", 0), "deal": self._value(result, "deal", 0),
                "volume": float(self._value(result, "volume", 0.0) or 0.0), "symbol": symbol,
                "side": intent.side, "requested_quantity": int(intent.quantity), "price": price,
                "environment": self.environment, "timestamp": datetime.now(timezone.utc).isoformat()}

    def close(self) -> None:
        if self._mt5 is not None and self._connected:
            self._mt5.shutdown()
        self._connected = False
