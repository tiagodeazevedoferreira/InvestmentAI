from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

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
ARM_ENV = "INVESTMENTAI_DEMO_EXECUTION_ARMED"


class ControlledDemoRunBlocked(RuntimeError):
    """Raised when the controlled DEMO runner cannot safely proceed."""


def _value(obj: Any, name: str, default: Any = None) -> Any:
    return obj.get(name, default) if isinstance(obj, Mapping) else getattr(obj, name, default)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Controlled DOTO/MT5 DEMO runner. Default mode is read-only readiness. "
            "Submission requires both --execute and an explicit execution arm environment variable."
        )
    )
    parser.add_argument("--terminal", default=os.getenv("MT5_TERMINAL_PATH", DEFAULT_TERMINAL))
    parser.add_argument("--login", type=int, default=int(os.getenv("MT5_DEMO_EXPECTED_LOGIN", DEFAULT_LOGIN)))
    parser.add_argument("--server", default=os.getenv("MT5_DEMO_EXPECTED_SERVER", DEFAULT_SERVER))
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--side", choices=("BUY", "SELL"), default="BUY")
    parser.add_argument("--volume", type=float, default=DEFAULT_VOLUME)
    parser.add_argument("--ledger", default=str(ROOT / ".runtime" / "demo-controlled.sqlite3"))
    parser.add_argument("--execute", action="store_true", help="Request the controlled DEMO submission path.")
    return parser.parse_args()


def _execution_armed() -> bool:
    return os.getenv(ARM_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _internal_state_from_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the current workstation state for the preflight boundary.

    This is intentionally a temporary bridge for the manual controlled runner.
    The scheduler and live trading paths do not consume it. Before the first
    real DEMO order, the application portfolio-state provider must replace this
    bridge so the post-execution provider reads the application's own state.
    """
    return {
        "cash": float(snapshot.get("cash", 0.0)),
        "positions": dict(snapshot.get("positions", {})),
        "open_orders": list(snapshot.get("open_orders", [])),
        "executions": list(snapshot.get("executions", [])),
    }


def main() -> int:
    args = parse_args()
    ledger_path = Path(args.ledger)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    if args.execute and not _execution_armed():
        print(
            f"CONTROLLED DEMO RUN: BLOCKED\n"
            f"--execute requires {ARM_ENV}=true; no broker submission attempted."
        )
        return 2

    broker = MetaTrader5DemoBroker(
        terminal_path=args.terminal,
        expected_login=args.login,
        expected_server=args.server,
        execution_enabled=bool(args.execute and _execution_armed()),
        max_volume=DEFAULT_VOLUME,
    )
    ledger = DemoOrderLedger(ledger_path)
    executor = AuthorizedDemoExecutor(
        broker,
        DemoAuthorizationGate(OperationalKillSwitch()),
    )
    service = ControlledDemoExecutionService(executor, ledger)
    initialized = False

    try:
        account = broker.connect()
        initialized = True
        if not account.trade_allowed or not account.trade_expert:
            raise ControlledDemoRunBlocked("MT5 DEMO account trading permissions are not both enabled")

        now = datetime.now(timezone.utc)
        before_snapshot = broker.reconciliation_snapshot(now, now)
        internal_before = _internal_state_from_snapshot(before_snapshot)
        intent = OrderIntent(args.symbol.upper(), args.side, args.volume)
        DemoOrderPreflight().validate(intent, environment="demo")

        if not args.execute:
            print("CONTROLLED DEMO RUN: READY")
            print(f"login: {account.login}")
            print(f"server: {account.server}")
            print(f"balance: {account.balance:.2f}")
            print(f"equity: {account.equity:.2f}")
            print(f"symbol: {intent.symbol}")
            print(f"side: {intent.side}")
            print(f"volume: {intent.quantity:.2f}")
            print("execution_enabled: False")
            print("order_send: NOT CALLED")
            print("next_gate: explicit --execute + execution arm")
            return 0

        def refresh_internal_state() -> Mapping[str, Any]:
            # Until portfolio accounting is wired to the execution service, this
            # bridge deliberately re-reads the workstation rather than reusing the
            # pre-execution object. It is still subject to post-reconciliation.
            refresh_now = datetime.now(timezone.utc)
            refreshed = broker.reconciliation_snapshot(refresh_now, refresh_now)
            return _internal_state_from_snapshot(refreshed)

        result = service.execute(
            intent,
            internal_before=internal_before,
            internal_after_provider=refresh_internal_state,
        )
        print("CONTROLLED DEMO RUN: SUCCESS")
        print(f"login: {account.login}")
        print(f"server: {account.server}")
        print(f"symbol: {intent.symbol}")
        print(f"side: {intent.side}")
        print(f"volume: {intent.quantity:.2f}")
        print(f"ledger_state: {result.record.state}")
        print(f"order_id: {result.record.order_id}")
        print(f"deal_id: {result.record.deal_id}")
        print(f"retcode: {_value(result.execution, 'retcode', '')}")
        print(f"post_reconciliation: {result.execution and result.execution.get('environment', 'demo')}")
        return 0
    except (ControlledDemoRunBlocked, Exception) as exc:
        print(f"CONTROLLED DEMO RUN: BLOCKED\nreason: {exc}")
        if not args.execute:
            print("order_send: NOT CALLED")
        return 1
    finally:
        if initialized:
            broker.close()


if __name__ == "__main__":
    raise SystemExit(main())
