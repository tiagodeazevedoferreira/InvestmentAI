from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


class MT5MarketDataError(RuntimeError):
    """Raised when MT5 market data cannot be read or verified."""


class MT5MarketDataModule(Protocol):
    def initialize(self, *args: Any, **kwargs: Any) -> bool: ...
    def shutdown(self) -> None: ...
    def last_error(self) -> Any: ...
    def symbol_select(self, symbol: str, enable: bool) -> bool: ...
    def symbol_info(self, symbol: str) -> Any: ...
    def symbol_info_tick(self, symbol: str) -> Any: ...


@dataclass(frozen=True)
class MT5Quote:
    symbol: str
    bid: float
    ask: float
    last: float
    time: int
    time_msc: int

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def timestamp(self) -> str:
        return datetime.fromtimestamp(self.time, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class MT5SymbolInfo:
    symbol: str
    digits: int
    point: float
    trade_mode: int


class MetaTrader5MarketDataGateway:
    """Read-only market data gateway for an authenticated Doto MT5 terminal.

    This gateway only selects symbols and reads market metadata/ticks. It does
    not submit, modify, or close trading orders.
    """

    def __init__(
        self,
        *,
        terminal_path: str,
        expected_login: int | None = None,
        expected_server: str = "DOTOGlobal-Real",
        mt5_module: MT5MarketDataModule | None = None,
    ) -> None:
        if not terminal_path:
            raise ValueError("terminal_path must not be empty")
        self.terminal_path = terminal_path
        self.expected_login = expected_login
        self.expected_server = expected_server
        self._mt5 = mt5_module
        self._connected = False

    def _module(self) -> MT5MarketDataModule:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5  # type: ignore
            except ImportError as exc:
                raise MT5MarketDataError(
                    "MetaTrader5 package is not installed"
                ) from exc
            self._mt5 = mt5
        return self._mt5

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def connect(self) -> None:
        mt5 = self._module()
        try:
            ok = bool(mt5.initialize(path=self.terminal_path, timeout=60_000))
        except TypeError:
            ok = bool(mt5.initialize(path=self.terminal_path))

        if not ok:
            raise MT5MarketDataError(f"MT5 initialize failed: {mt5.last_error()}")

        self._connected = True

        account = mt5.account_info()
        terminal = mt5.terminal_info() if hasattr(mt5, "terminal_info") else None

        if account is None:
            self.close()
            raise MT5MarketDataError("MT5 account_info returned no account")

        if terminal is not None and not bool(self._value(terminal, "connected", False)):
            self.close()
            raise MT5MarketDataError("MT5 terminal is not connected")

        if self.expected_login is not None:
            login = int(self._value(account, "login", 0))
            if login != self.expected_login:
                self.close()
                raise MT5MarketDataError(
                    f"Unexpected MT5 account: {login}; expected {self.expected_login}"
                )

        server = str(self._value(account, "server", ""))
        if server != self.expected_server:
            self.close()
            raise MT5MarketDataError(
                f"Unexpected MT5 server: {server!r}; expected {self.expected_server!r}"
            )

    def quote(self, symbol: str) -> MT5Quote:
        if not self._connected:
            raise MT5MarketDataError("MT5 gateway is not connected")
        normalized = self._normalize_symbol(symbol)
        mt5 = self._module()

        if not bool(mt5.symbol_select(normalized, True)):
            raise MT5MarketDataError(f"Unable to select MT5 symbol: {normalized}")

        info = mt5.symbol_info(normalized)
        if info is None:
            raise MT5MarketDataError(f"MT5 symbol not found: {normalized}")

        tick = mt5.symbol_info_tick(normalized)
        if tick is None:
            raise MT5MarketDataError(f"No MT5 tick available for: {normalized}")

        return MT5Quote(
            symbol=normalized,
            bid=float(self._value(tick, "bid", 0.0)),
            ask=float(self._value(tick, "ask", 0.0)),
            last=float(self._value(tick, "last", 0.0)),
            time=int(self._value(tick, "time", 0)),
            time_msc=int(self._value(tick, "time_msc", 0)),
        )

    def symbol_info(self, symbol: str) -> MT5SymbolInfo:
        if not self._connected:
            raise MT5MarketDataError("MT5 gateway is not connected")
        normalized = self._normalize_symbol(symbol)
        mt5 = self._module()

        if not bool(mt5.symbol_select(normalized, True)):
            raise MT5MarketDataError(f"Unable to select MT5 symbol: {normalized}")

        info = mt5.symbol_info(normalized)
        if info is None:
            raise MT5MarketDataError(f"MT5 symbol not found: {normalized}")

        return MT5SymbolInfo(
            symbol=normalized,
            digits=int(self._value(info, "digits", 0)),
            point=float(self._value(info, "point", 0.0)),
            trade_mode=int(self._value(info, "trade_mode", 0)),
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper() if symbol else ""
        if not normalized:
            raise ValueError("Symbol is required")
        return normalized

    def close(self) -> None:
        if self._mt5 is not None and self._connected:
            self._mt5.shutdown()
        self._connected = False
