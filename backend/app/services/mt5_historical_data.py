from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


class MT5HistoricalDataError(RuntimeError):
    """Raised when historical MT5 data cannot be retrieved."""


class MT5HistoricalGateway(Protocol):
    def initialize(self, *args: Any, **kwargs: Any) -> bool: ...

    def shutdown(self) -> None: ...

    def last_error(self) -> Any: ...

    def terminal_info(self) -> Any: ...

    def account_info(self) -> Any: ...

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> Any: ...

    def symbol_select(self, symbol: str, enable: bool) -> bool: ...


@dataclass(frozen=True)
class MT5Candle:
    symbol: str
    timeframe: str
    time: int
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class MetaTrader5HistoricalDataGateway:
    """Read-only gateway for historical candles from the Doto MT5 terminal.

    This gateway only reads market data. It never places or modifies orders.
    """

    TIMEFRAMES: dict[str, int] = {
        "M1": 1,
        "M2": 2,
        "M3": 3,
        "M4": 4,
        "M5": 5,
        "M6": 6,
        "M10": 10,
        "M12": 12,
        "M15": 15,
        "M20": 20,
        "M30": 30,
        "H1": 16385,
        "H2": 16386,
        "H3": 16387,
        "H4": 16388,
        "H6": 16390,
        "H8": 16392,
        "H12": 16396,
        "D1": 16408,
        "W1": 32769,
        "MN1": 49153,
    }

    def __init__(
        self,
        *,
        terminal_path: str,
        expected_login: int | None = None,
        expected_server: str = "DOTOGlobal-Real",
        mt5_module: Any | None = None,
    ) -> None:
        if not terminal_path:
            raise ValueError("terminal_path must not be empty")

        self.terminal_path = terminal_path
        self.expected_login = expected_login
        self.expected_server = expected_server
        self._mt5 = mt5_module
        self._connected = False

    def _module(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                raise MT5HistoricalDataError(
                    "MetaTrader5 package is not installed"
                ) from exc

            self._mt5 = mt5

        return self._mt5

    @staticmethod
    def _value(
        obj: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    def connect(self) -> None:
        mt5 = self._module()

        try:
            ok = bool(
                mt5.initialize(
                    path=self.terminal_path,
                    timeout=60_000,
                )
            )
        except TypeError:
            ok = bool(mt5.initialize(path=self.terminal_path))

        if not ok:
            raise MT5HistoricalDataError(
                f"MT5 initialize failed: {mt5.last_error()}"
            )

        self._connected = True

        account = mt5.account_info()
        terminal = mt5.terminal_info()

        if account is None:
            self.close()
            raise MT5HistoricalDataError(
                "MT5 account_info returned no account"
            )

        if terminal is None or not bool(
            self._value(terminal, "connected", False)
        ):
            self.close()
            raise MT5HistoricalDataError(
                "Doto MT5 terminal is not connected"
            )

        login = int(self._value(account, "login", 0))
        server = str(self._value(account, "server", ""))

        if (
            self.expected_login is not None
            and login != self.expected_login
        ):
            self.close()
            raise MT5HistoricalDataError(
                f"Unexpected MT5 account: {login}; "
                f"expected {self.expected_login}"
            )

        if server != self.expected_server:
            self.close()
            raise MT5HistoricalDataError(
                f"Unexpected MT5 server: {server!r}; "
                f"expected {self.expected_server!r}"
            )

    def candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
        start_pos: int = 0,
    ) -> list[MT5Candle]:
        if not symbol:
            raise ValueError("symbol must not be empty")

        timeframe_key = timeframe.upper()

        if timeframe_key not in self.TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported values: {', '.join(self.TIMEFRAMES)}"
            )

        if count < 1:
            raise ValueError("count must be greater than zero")

        if count > 5000:
            raise ValueError("count must not exceed 5000")

        if start_pos < 0:
            raise ValueError("start_pos must not be negative")

        mt5 = self._module()

        if not self._connected:
            self.connect()

        if not mt5.symbol_select(symbol, True):
            raise MT5HistoricalDataError(
                f"Unable to select symbol {symbol!r}: {mt5.last_error()}"
            )

        rates = mt5.copy_rates_from_pos(
            symbol,
            self.TIMEFRAMES[timeframe_key],
            start_pos,
            count,
        )

        if rates is None:
            raise MT5HistoricalDataError(
                f"Unable to retrieve candles for {symbol} "
                f"{timeframe_key}: {mt5.last_error()}"
            )

        candles: list[MT5Candle] = []

        for rate in rates:
            timestamp = int(rate["time"])
            dt = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            )

            candles.append(
                MT5Candle(
                    symbol=symbol,
                    timeframe=timeframe_key,
                    time=timestamp,
                    timestamp=dt.isoformat(),
                    open=float(rate["open"]),
                    high=float(rate["high"]),
                    low=float(rate["low"]),
                    close=float(rate["close"]),
                    tick_volume=int(rate["tick_volume"]),
                    spread=int(rate["spread"]),
                    real_volume=int(rate["real_volume"]),
                )
            )

        return candles

    def close(self) -> None:
        if self._mt5 is not None and self._connected:
            self._mt5.shutdown()

        self._connected = False
