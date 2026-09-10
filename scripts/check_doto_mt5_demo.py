from __future__ import annotations

import argparse
import os

from app.services.mt5_demo_broker import MT5DemoExecutionError, MetaTrader5DemoBroker


DEFAULT_TERMINAL = r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only preflight validation for the configured DOTO MT5 DEMO account."
    )
    parser.add_argument("--terminal", default=os.getenv("MT5_DEMO_TERMINAL_PATH", DEFAULT_TERMINAL))
    parser.add_argument("--login", type=int, default=int(os.environ["MT5_DEMO_EXPECTED_LOGIN"]) if os.getenv("MT5_DEMO_EXPECTED_LOGIN") else None)
    parser.add_argument("--server", default=os.getenv("MT5_DEMO_EXPECTED_SERVER"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.login is None or not args.server:
        print("DEMO preflight blocked: provide --login and --server (or MT5_DEMO_EXPECTED_LOGIN/MT5_DEMO_EXPECTED_SERVER).")
        return 2

    broker = MetaTrader5DemoBroker(
        terminal_path=args.terminal,
        expected_login=args.login,
        expected_server=args.server,
        execution_enabled=False,
    )
    try:
        account = broker.connect()
        print("MT5 DEMO preflight: OK")
        print(f"login: {account.login}")
        print(f"server: {account.server}")
        print(f"currency: {account.currency}")
        print(f"balance: {account.balance:.2f}")
        print(f"equity: {account.equity:.2f}")
        print(f"trade_allowed: {account.trade_allowed}")
        print(f"trade_expert: {account.trade_expert}")
        print("execution_enabled: False")
        print("order submission: NOT ATTEMPTED")
        return 0
    except (MT5DemoExecutionError, ValueError) as exc:
        print(f"MT5 DEMO preflight failed: {exc}")
        return 1
    finally:
        broker.close()


if __name__ == "__main__":
    raise SystemExit(main())
