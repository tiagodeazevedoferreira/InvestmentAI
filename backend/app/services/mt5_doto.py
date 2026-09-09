from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DotoMT5ConnectionError(RuntimeError):
    """Raised when the Doto MT5 terminal cannot be connected or verified."""


class MT5ConnectionGateway(Protocol):
    def initialize(self, *args: Any, **kwargs: Any) -> bool: ...
    def shutdown(self) -> None: ...
    def last_error(self) -> Any: ...
    def terminal_info(self) -> Any: ...
    def account_info(self) -> Any: ...


@dataclass(frozen=True)
class DotoMT5AccountSnapshot:
    login: int
    server: str
    company: str
    currency: str
    balance: float
    equity: float
    trade_allowed: bool
    trade_expert: bool


class MetaTrader5DotoGateway:
    """Connection-only gateway for the Doto Global MT5 terminal.

    The gateway intentionally relies on the already authenticated desktop
    terminal. It does not store or request a password and does not place orders.
    """

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
                import MetaTrader5 as mt5  # type: ignore
            except ImportError as exc:
                raise DotoMT5ConnectionError(
                    "MetaTrader5 package is not installed"
                ) from exc
            self._mt5 = mt5
        return self._mt5

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def connect(self) -> DotoMT5AccountSnapshot:
        mt5 = self._module()
        try:
            ok = bool(mt5.initialize(path=self.terminal_path, timeout=60_000))
        except TypeError:
            # Test doubles and older wrappers may not accept timeout.
            ok = bool(mt5.initialize(path=self.terminal_path))

        if not ok:
            raise DotoMT5ConnectionError(
                f"MT5 initialize failed: {mt5.last_error()}"
            )

        self._connected = True
        account = mt5.account_info()
        terminal = mt5.terminal_info()

        if account is None:
            self.close()
            raise DotoMT5ConnectionError("MT5 account_info returned no account")

        if terminal is None or not bool(self._value(terminal, "connected", False)):
            self.close()
            raise DotoMT5ConnectionError("Doto MT5 terminal is not connected")

        login = int(self._value(account, "login", 0))
        server = str(self._value(account, "server", ""))

        if self.expected_login is not None and login != self.expected_login:
            self.close()
            raise DotoMT5ConnectionError(
                f"Unexpected MT5 account: {login}; expected {self.expected_login}"
            )

        if server != self.expected_server:
            self.close()
            raise DotoMT5ConnectionError(
                f"Unexpected MT5 server: {server!r}; expected {self.expected_server!r}"
            )

        return DotoMT5AccountSnapshot(
            login=login,
            server=server,
            company=str(self._value(account, "company", "")),
            currency=str(self._value(account, "currency", "")),
            balance=float(self._value(account, "balance", 0.0)),
            equity=float(self._value(account, "equity", 0.0)),
            trade_allowed=bool(self._value(account, "trade_allowed", False)),
            trade_expert=bool(self._value(account, "trade_expert", False)),
        )

    def close(self) -> None:
        if self._mt5 is not None and self._connected:
            self._mt5.shutdown()
        self._connected = False
