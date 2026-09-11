"""Read-only validation of DEMO restart/recovery against real MT5 history.

This harness never calls order_send(). It creates a temporary ledger record that
represents an interrupted submission, asks the authenticated DOTO/MT5 DEMO
adapter for targeted broker evidence, and verifies that exact deal evidence
promotes the record to FILLED. It also verifies that unrelated/missing evidence
remains SUBMITTED.
"""

from __future__ import annotations

import argparse
import gc
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from app.services.controlled_demo_execution import ControlledDemoExecutionService
from app.services.demo_authorization import DemoAuthorizationGate
from app.services.demo_execution import AuthorizedDemoExecutor
from app.services.demo_ledger import DemoOrderLedger
from app.services.mt5_demo_broker import MetaTrader5DemoBroker
from app.services.operational_kill_switch import OperationalKillSwitch


TERMINAL_PATH = r"C:\Users\tiago.ferreira\AppData\Roaming\DOTO Global MT5 Terminal\terminal64.exe"
EXPECTED_LOGIN = 5344431
EXPECTED_SERVER = "DOTOGlobal-Real"
ORDER_ID = "29453207"
DEAL_ID = "28862296"
SYMBOL = "EURUSD"
QUANTITY = 0.01


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate read-only DEMO restart/recovery")
    parser.add_argument("--terminal-path", default=TERMINAL_PATH)
    parser.add_argument("--order-id", default=ORDER_ID)
    parser.add_argument("--deal-id", default=DEAL_ID)
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--quantity", type=float, default=QUANTITY)
    args = parser.parse_args()

    broker = MetaTrader5DemoBroker(
        terminal_path=args.terminal_path,
        expected_login=EXPECTED_LOGIN,
        expected_server=EXPECTED_SERVER,
        execution_enabled=False,
    )
    account = broker.connect()
    try:
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory(prefix="investmentai-demo-recovery-") as temp_dir:
            ledger = DemoOrderLedger(Path(temp_dir) / "demo.sqlite3")
            ledger.create("confirmed", args.symbol, "BUY", args.quantity, now=now)
            ledger.transition("confirmed", "AUTHORIZED", now=now)
            ledger.transition(
                "confirmed",
                "SUBMITTED",
                now=now,
                order_id=args.order_id,
                deal_id=args.deal_id,
            )

            ledger.create("ambiguous", args.symbol, "BUY", args.quantity, now=now)
            ledger.transition("ambiguous", "AUTHORIZED", now=now)
            ledger.transition(
                "ambiguous",
                "SUBMITTED",
                now=now,
                order_id="unknown-order",
                deal_id="unknown-deal",
            )

            executor = AuthorizedDemoExecutor(
                broker,
                DemoAuthorizationGate(OperationalKillSwitch()),
            )
            service = ControlledDemoExecutionService(executor, ledger)
            recovered = service.recover_pending(
                lambda record: broker.reconciliation_snapshot_after_execution(record.execution or {
                    "order": record.order_id,
                    "deal": record.deal_id,
                })
            )

            confirmed = ledger.get("confirmed")
            ambiguous = ledger.get("ambiguous")
            if confirmed.state != "FILLED":
                raise RuntimeError(f"confirmed recovery failed: {confirmed.state}")
            if ambiguous.state != "SUBMITTED":
                raise RuntimeError(f"ambiguous recovery was not fail-closed: {ambiguous.state}")

            print("DEMO RECOVERY VALIDATION: SUCCESS")
            print(f"login: {account.login}")
            print(f"server: {account.server}")
            print(f"symbol: {args.symbol}")
            print(f"confirmed_order_id: {args.order_id}")
            print(f"confirmed_deal_id: {args.deal_id}")
            print(f"confirmed_state: {confirmed.state}")
            print(f"ambiguous_state: {ambiguous.state}")
            print(f"recovered_records: {len(recovered)}")
            print("order_send: NOT CALLED")
            print("temporary ledger: discarded")

            # The ledger intentionally opens short-lived sqlite connections.
            # Release all local references before TemporaryDirectory cleanup;
            # this avoids a Windows file-lock race when sqlite objects are
            # finalized after the temporary directory cleanup starts.
            del recovered, confirmed, ambiguous, service, executor, ledger
            gc.collect()
            return 0
    finally:
        broker.close()


if __name__ == "__main__":
    raise SystemExit(main())
