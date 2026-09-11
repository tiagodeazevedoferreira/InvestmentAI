from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.controlled_demo_execution import ControlledDemoExecutionService
from app.services.demo_authorization import DemoAuthorizationGate
from app.services.demo_execution import AuthorizedDemoExecutor
from app.services.demo_ledger import DemoOrderLedger
from app.services.demo_order_preflight import DemoOrderPreflight
from app.services.mt5_demo_broker import MetaTrader5DemoBroker
from app.services.operational_kill_switch import OperationalKillSwitch
from app.services.order_manager import OrderIntent

DEFAULT_TERMINAL = r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe"
DEFAULT_LOGIN = 5344431
DEFAULT_SERVER = "DOTOGlobal-Real"
DEFAULT_SYMBOL = "EURUSD"
DEFAULT_VOLUME = 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only controlled DEMO execution-path preflight; broker submission remains disabled."
    )
    parser.add_argument("--terminal", default=os.getenv("MT5_TERMINAL_PATH", DEFAULT_TERMINAL))
    parser.add_argument("--login", type=int, default=int(os.getenv("MT5_DEMO_EXPECTED_LOGIN", DEFAULT_LOGIN)))
    parser.add_argument("--server", default=os.getenv("MT5_DEMO_EXPECTED_SERVER", DEFAULT_SERVER))
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--side", choices=["BUY", "SELL"], default="BUY")
    parser.add_argument("--volume", type=float, default=DEFAULT_VOLUME)
    parser.add_argument("--ledger", default=str(ROOT / ".runtime" / "demo-preflight.sqlite3"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ledger_path = Path(args.ledger)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    broker = MetaTrader5DemoBroker(
        terminal_path=args.terminal,
        expected_login=args.login,
        expected_server=args.server,
        execution_enabled=False,
        max_volume=DEFAULT_VOLUME,
    )
    ledger = DemoOrderLedger(ledger_path)
    executor = AuthorizedDemoExecutor(
        broker,
        DemoAuthorizationGate(OperationalKillSwitch()),
    )
    service = ControlledDemoExecutionService(executor, ledger)

    try:
        account = broker.connect()
        if not account.trade_allowed or not account.trade_expert:
            raise RuntimeError("MT5 DEMO account trading permissions are not both enabled")

        now = datetime.now(timezone.utc)
        snapshot = broker.reconciliation_snapshot(now, now)
        intent = OrderIntent(args.symbol.upper(), args.side, args.volume)
        DemoOrderPreflight().validate(intent, environment="demo")

        intent_id = None
        try:
            result = service.execute(
                intent,
                internal_before=snapshot,
                internal_after=snapshot,
            )
            intent_id = result.record.intent_id
            print("CONTROLLED DEMO PREFLIGHT: UNEXPECTED SUCCESS")
            print(json.dumps({"record": result.record.state}, indent=2))
            return 2
        except Exception as exc:
            # With execution_enabled=False, authorization must pass and broker.submit
            # must be the first blocking point. No MT5 order_send can occur here.
            records = ledger.list_recent(limit=1)
            record = records[0] if records else None
            intent_id = record.intent_id if record else None
            if record is None or record.state != "AUTHORIZED":
                print("CONTROLLED DEMO PREFLIGHT: FAILED", file=sys.stderr)
                print(f"expected ledger state AUTHORIZED before blocked submit; got {record}", file=sys.stderr)
                return 1
            if "DEMO execution is disabled" not in (record.error or ""):
                print("CONTROLLED DEMO PREFLIGHT: FAILED", file=sys.stderr)
                print(f"unexpected blocker: {record.error}", file=sys.stderr)
                return 1
            print("CONTROLLED DEMO PREFLIGHT: OK")
            print(f"login: {account.login}")
            print(f"server: {account.server}")
            print(f"balance: {account.balance:.2f}")
            print(f"equity: {account.equity:.2f}")
            print(f"symbol: {intent.symbol}")
            print(f"side: {intent.side}")
            print(f"volume: {intent.quantity:.2f}")
            print("authorization: ALLOWED")
            print("ledger_state: AUTHORIZED")
            print("execution_enabled: False")
            print("order_send: NOT CALLED")
            print(f"intent_id: {intent_id}")
            return 0
    finally:
        broker.close()


if __name__ == "__main__":
    raise SystemExit(main())
