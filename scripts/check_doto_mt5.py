from __future__ import annotations

import os

from app.services.mt5_doto import DotoMT5ConnectionError, MetaTrader5DotoGateway


DEFAULT_TERMINAL = r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe"


def main() -> int:
    terminal_path = os.getenv("MT5_TERMINAL_PATH", DEFAULT_TERMINAL)
    login_raw = os.getenv("MT5_EXPECTED_LOGIN", "5344431")
    login = int(login_raw) if login_raw else None
    server = os.getenv("MT5_EXPECTED_SERVER", "DOTOGlobal-Real")

    gateway = MetaTrader5DotoGateway(
        terminal_path=terminal_path,
        expected_login=login,
        expected_server=server,
    )
    try:
        account = gateway.connect()
    except DotoMT5ConnectionError as exc:
        print(f"DOTO MT5 connection failed: {exc}")
        return 1

    try:
        print("DOTO MT5 connection: OK")
        print(f"login: {account.login}")
        print(f"server: {account.server}")
        print(f"company: {account.company}")
        print(f"currency: {account.currency}")
        print(f"balance: {account.balance:.2f}")
        print(f"equity: {account.equity:.2f}")
        print(f"trade_allowed: {account.trade_allowed}")
        print(f"trade_expert: {account.trade_expert}")
    finally:
        gateway.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
