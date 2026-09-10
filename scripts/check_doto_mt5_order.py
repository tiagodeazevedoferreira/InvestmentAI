from __future__ import annotations

import argparse
import os
from typing import Any


DEFAULT_TERMINAL = r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe"
DEFAULT_LOGIN = 5344431
DEFAULT_SERVER = "DOTOGlobal-Real"
DEFAULT_SYMBOL = "EURUSD"
DEFAULT_SIDE = "BUY"
DEFAULT_VOLUME = 0.01


class OrderCheckBlocked(RuntimeError):
    """Raised when the read-only MT5 order preflight cannot safely proceed."""


def _value(obj: Any, name: str, default: Any = None) -> Any:
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def build_request(mt5: Any, *, symbol: str, side: str, volume: float) -> dict[str, Any]:
    symbol = symbol.strip().upper()
    side = side.strip().upper()
    if not symbol:
        raise OrderCheckBlocked("symbol cannot be empty")
    if side not in {"BUY", "SELL"}:
        raise OrderCheckBlocked("side must be BUY or SELL")
    if volume <= 0 or volume > DEFAULT_VOLUME:
        raise OrderCheckBlocked(f"volume must be > 0 and <= {DEFAULT_VOLUME}")

    if not mt5.symbol_select(symbol, True):
        raise OrderCheckBlocked(f"cannot select MT5 symbol: {symbol}")
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if info is None or tick is None:
        raise OrderCheckBlocked(f"MT5 market data unavailable for {symbol}")

    volume_min = float(_value(info, "volume_min", 0.0) or 0.0)
    volume_max = float(_value(info, "volume_max", 0.0) or 0.0)
    volume_step = float(_value(info, "volume_step", 0.0) or 0.0)
    if volume_min > 0 and volume < volume_min:
        raise OrderCheckBlocked(f"volume {volume} is below symbol minimum {volume_min}")
    if volume_max > 0 and volume > volume_max:
        raise OrderCheckBlocked(f"volume {volume} exceeds symbol maximum {volume_max}")
    if volume_step > 0:
        steps = round(volume / volume_step)
        if abs(volume - steps * volume_step) > 1e-9:
            raise OrderCheckBlocked(f"volume {volume} is not aligned to symbol step {volume_step}")

    order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
    price = float(_value(tick, "ask" if side == "BUY" else "bid", 0.0))
    if price <= 0:
        raise OrderCheckBlocked("invalid market price")

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "comment": "InvestmentAI-DEMO-PREFLIGHT",
    }


def run_order_check(mt5: Any, *, expected_login: int, expected_server: str,
                    symbol: str, side: str, volume: float) -> dict[str, Any]:
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    if account is None:
        raise OrderCheckBlocked("MT5 account_info returned no account")
    if terminal is None or not bool(_value(terminal, "connected", False)):
        raise OrderCheckBlocked("MT5 terminal is not connected")

    login = int(_value(account, "login", 0))
    server = str(_value(account, "server", ""))
    if login != expected_login:
        raise OrderCheckBlocked(f"account mismatch: {login}; expected {expected_login}")
    if server != expected_server:
        raise OrderCheckBlocked(f"server mismatch: {server!r}; expected {expected_server!r}")
    if not bool(_value(account, "trade_allowed", False)):
        raise OrderCheckBlocked("MT5 account does not report trading as allowed")
    if not bool(_value(account, "trade_expert", False)):
        raise OrderCheckBlocked("MT5 account does not report expert trading as allowed")

    request = build_request(mt5, symbol=symbol, side=side, volume=volume)
    check = mt5.order_check(request)
    if check is None:
        raise OrderCheckBlocked("MT5 order_check returned None")
    retcode = _value(check, "retcode", None)
    comment = str(_value(check, "comment", ""))
    if retcode is not None and int(retcode) != 0:
        raise OrderCheckBlocked(f"MT5 order_check rejected request: {retcode} {comment}".strip())

    return {
        "login": login,
        "server": server,
        "symbol": request["symbol"],
        "side": side.strip().upper(),
        "volume": request["volume"],
        "price": request["price"],
        "retcode": int(retcode) if retcode is not None else None,
        "comment": comment,
        "order_send_called": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only MT5 order_check preflight; order_send is never called."
    )
    parser.add_argument("--terminal", default=os.getenv("MT5_DEMO_TERMINAL_PATH", DEFAULT_TERMINAL))
    parser.add_argument("--login", type=int, default=int(os.getenv("MT5_DEMO_EXPECTED_LOGIN", DEFAULT_LOGIN)))
    parser.add_argument("--server", default=os.getenv("MT5_DEMO_EXPECTED_SERVER", DEFAULT_SERVER))
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--side", choices=("BUY", "SELL"), default=DEFAULT_SIDE)
    parser.add_argument("--volume", type=float, default=DEFAULT_VOLUME)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError:
        print("MT5 order preflight failed: MetaTrader5 package is not installed")
        return 1

    initialized = False
    try:
        try:
            initialized = bool(mt5.initialize(path=args.terminal, timeout=60_000))
        except TypeError:
            initialized = bool(mt5.initialize(path=args.terminal))
        if not initialized:
            print(f"MT5 order preflight failed: initialize: {mt5.last_error()}")
            return 1

        result = run_order_check(
            mt5,
            expected_login=args.login,
            expected_server=args.server,
            symbol=args.symbol,
            side=args.side,
            volume=args.volume,
        )
        print("MT5 order_check preflight: OK")
        for key, value in result.items():
            print(f"{key}: {value}")
        print("execution_enabled: False")
        print("order_send: NOT CALLED")
        return 0
    except (OrderCheckBlocked, ValueError) as exc:
        print(f"MT5 order_check preflight failed: {exc}")
        print("order_send: NOT CALLED")
        return 1
    finally:
        if initialized:
            mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
