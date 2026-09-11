from datetime import datetime, timezone

import pytest

from app.services.controlled_demo_execution import ControlledDemoExecutionService
from app.services.demo_authorization import DemoAuthorizationGate
from app.services.demo_execution import AuthorizedDemoExecutor, DemoExecutionBlocked
from app.services.demo_ledger import DemoOrderLedger
from app.services.operational_kill_switch import OperationalKillSwitch
from app.services.order_manager import OrderIntent


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def state(cash=1000.0, quantity=10, executions=None):
    return {"cash": cash, "positions": {"PETR4": {"quantity": quantity}},
            "open_orders": [], "executions": executions or []}


def snapshot(value):
    return {**value, "captured_at": NOW.isoformat()}


class Broker:
    environment = "demo"

    def __init__(self, snapshots):
        self.snapshots = iter(snapshots)
        self.submissions = []

    def reconciliation_snapshot(self, date_from, date_to):
        return next(self.snapshots)

    def submit(self, intent):
        self.submissions.append(intent)
        return {"order": 123, "deal": 456, "retcode": 10009, "accepted": True, "symbol": intent.symbol}


def test_controlled_service_persists_full_success_lifecycle(tmp_path):
    before = state()
    after = state(cash=900.0, quantity=20, executions=[{"execution_id": "456"}])
    broker = Broker([snapshot(before), snapshot(after)])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)

    result = service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                             internal_after_provider=lambda: after)

    assert result.record.state == "FILLED"
    assert result.record.order_id == "123"
    assert result.record.deal_id == "456"
    assert result.record.execution["retcode"] == 10009
    assert [item.state for item in [ledger.get("intent-1")]] == ["FILLED"]


def test_controlled_service_leaves_uncertain_execution_recoverable(tmp_path):
    before = state()
    after = state(cash=999.0, quantity=20, executions=[{"execution_id": "456"}])
    external_after = state(cash=999.0, quantity=19, executions=[{"execution_id": "456"}])
    broker = Broker([snapshot(before), snapshot(external_after)])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)

    with pytest.raises(Exception, match="post-execution reconciliation failed"):
        service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                        internal_after_provider=lambda: after)

    record = ledger.get("intent-1")
    assert record.state == "SUBMITTED"
    assert record.deal_id == "456"
    assert record.error


def test_post_execution_internal_state_is_refreshed_after_submission(tmp_path):
    before = state()
    refreshed = state(cash=900.0, quantity=20, executions=[{"execution_id": "456"}])
    broker = Broker([snapshot(before), snapshot(refreshed)])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    calls = []

    def provider():
        calls.append("refreshed")
        return refreshed

    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)
    result = service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                             internal_after_provider=provider)

    assert result.record.state == "FILLED"
    assert calls == ["refreshed"]
    assert broker.submissions


def test_invalid_post_execution_internal_state_blocks_success_after_submission(tmp_path):
    before = state()
    broker = Broker([snapshot(before), snapshot(before)])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)

    with pytest.raises(DemoExecutionBlocked, match="post-execution internal state is invalid"):
        service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                        internal_after_provider=lambda: {"cash": 1000.0})

    record = ledger.get("intent-1")
    assert record.state == "SUBMITTED"
    assert record.deal_id == "456"
    assert record.error
