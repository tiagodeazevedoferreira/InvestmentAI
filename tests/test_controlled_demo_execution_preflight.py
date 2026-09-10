from datetime import datetime, timezone

import pytest

from app.services.controlled_demo_execution import ControlledDemoExecutionService
from app.services.demo_authorization import DemoAuthorizationGate
from app.services.demo_execution import AuthorizedDemoExecutor
from app.services.demo_ledger import DemoOrderLedger
from app.services.operational_kill_switch import OperationalKillSwitch
from app.services.order_manager import OrderIntent


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


class Broker:
    environment = "demo"

    def __init__(self):
        self.snapshots = 0
        self.submissions = 0

    def reconciliation_snapshot(self, date_from, date_to):
        self.snapshots += 1
        return {"captured_at": NOW.isoformat(), "cash": 1000.0, "positions": {}, "open_orders": [], "executions": []}

    def submit(self, intent):
        self.submissions += 1
        return {"retcode": 10009, "order": 1, "deal": 2, "accepted": True}


def test_oversized_order_never_reaches_broker(tmp_path):
    broker = Broker()
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    service = ControlledDemoExecutionService(executor, DemoOrderLedger(tmp_path / "demo.sqlite3"), now=lambda: NOW)

    state = {"cash": 1000.0, "positions": {}, "open_orders": [], "executions": []}
    with pytest.raises(ValueError, match="preflight limit"):
        service.execute(OrderIntent("EURUSD", "BUY", 0.010001), internal_before=state, internal_after=state)

    assert broker.snapshots == 0
    assert broker.submissions == 0
