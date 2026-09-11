from datetime import datetime, timedelta, timezone

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

    def __init__(self, snapshots, submission=None):
        self.snapshots = iter(snapshots)
        self.submissions = []
        self.submission = submission or {"order": 123, "deal": 456, "retcode": 10009, "accepted": True, "symbol": "PETR4"}

    def reconciliation_snapshot(self, date_from, date_to):
        return next(self.snapshots)

    def submit(self, intent):
        self.submissions.append(intent)
        return dict(self.submission)


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


def test_known_broker_rejection_is_terminal_even_if_post_reconciliation_fails(tmp_path):
    before = state()
    after = state()
    broker = Broker(
        [snapshot(before), snapshot(before)],
        submission={"order": 0, "deal": 0, "retcode": 10027, "accepted": False, "symbol": "PETR4"},
    )
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)

    original_snapshot = broker.reconciliation_snapshot
    calls = {"count": 0}

    def failing_second_snapshot(date_from, date_to):
        calls["count"] += 1
        if calls["count"] == 2:
            return {**snapshot(before), "captured_at": (NOW + timedelta(seconds=1)).isoformat()}
        return original_snapshot(date_from, date_to)

    broker.reconciliation_snapshot = failing_second_snapshot

    with pytest.raises(DemoExecutionBlocked, match="post-execution reconciliation failed"):
        service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                        internal_after_provider=lambda: after)

    record = ledger.get("intent-1")
    assert record.state == "REJECTED"
    assert record.execution["retcode"] == 10027
    assert record.execution["accepted"] is False
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


def test_post_snapshot_capture_is_not_marked_future_when_broker_captures_after_request(tmp_path):
    before = state()
    after = state(cash=900.0, quantity=20, executions=[{"execution_id": "456"}])

    class Clock:
        def __init__(self):
            self.current = NOW

        def __call__(self):
            value = self.current
            self.current += timedelta(microseconds=100)
            return value

    clock = Clock()

    class CapturingBroker(Broker):
        def __init__(self):
            super().__init__([snapshot(before), snapshot(after)])
            self.capture_calls = 0

        def reconciliation_snapshot(self, date_from, date_to):
            self.capture_calls += 1
            if self.capture_calls == 1:
                return {**before, "captured_at": date_to.isoformat()}
            return {**after, "captured_at": (date_to + timedelta(microseconds=100)).isoformat()}

    broker = CapturingBroker()
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=clock)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=clock)

    result = service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                             internal_after_provider=lambda: after)

    assert result.record.state == "FILLED"
    assert broker.capture_calls == 2


def test_recover_pending_after_restart_promotes_confirmed_submission_without_broker_submit(tmp_path):
    path = tmp_path / "demo.sqlite3"
    ledger = DemoOrderLedger(path)
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, order_id="29453207", deal_id="28862296")

    restarted_ledger = DemoOrderLedger(path)
    broker = Broker([])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    service = ControlledDemoExecutionService(executor, restarted_ledger, now=lambda: NOW)

    recovered = service.recover_pending(
        lambda record: {"executions": [{"execution_id": record.deal_id, "order_id": record.order_id}]}
    )

    assert recovered[0].state == "FILLED"
    assert restarted_ledger.get("intent-1").state == "FILLED"
    assert broker.submissions == []


def test_recover_pending_after_restart_keeps_unconfirmed_submission_and_does_not_submit(tmp_path):
    path = tmp_path / "demo.sqlite3"
    ledger = DemoOrderLedger(path)
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, order_id="order-1", deal_id="deal-1")

    restarted_ledger = DemoOrderLedger(path)
    broker = Broker([])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    service = ControlledDemoExecutionService(executor, restarted_ledger, now=lambda: NOW)

    recovered = service.recover_pending(lambda record: {"executions": [], "positions": {"EURUSD": {"quantity": 0.01}}})

    assert recovered[0].state == "SUBMITTED"
    assert restarted_ledger.get("intent-1").state == "SUBMITTED"
    assert broker.submissions == []


def test_recovery_evidence_failure_keeps_submission_pending_and_continues(tmp_path):
    path = tmp_path / "demo.sqlite3"
    ledger = DemoOrderLedger(path)
    for intent_id, deal_id in (("intent-1", "deal-1"), ("intent-2", "deal-2")):
        ledger.create(intent_id, "EURUSD", "BUY", 0.01, now=NOW)
        ledger.transition(intent_id, "AUTHORIZED", now=NOW)
        ledger.transition(intent_id, "SUBMITTED", now=NOW, order_id=f"order-{intent_id}", deal_id=deal_id)

    restarted_ledger = DemoOrderLedger(path)
    broker = Broker([])
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    service = ControlledDemoExecutionService(executor, restarted_ledger, now=lambda: NOW)
    calls = []

    def evidence(record):
        calls.append(record.intent_id)
        if record.intent_id == "intent-1":
            raise TimeoutError("history lookup timeout")
        return {"executions": [{"execution_id": "deal-2", "order_id": "order-intent-2"}]}

    recovered = service.recover_pending(evidence)

    assert [record.state for record in recovered] == ["SUBMITTED", "FILLED"]
    assert restarted_ledger.get("intent-1").error == "history lookup timeout"
    assert restarted_ledger.get("intent-2").state == "FILLED"
    assert calls == ["intent-1", "intent-2"]
    assert broker.submissions == []


def test_submission_exception_after_authorization_becomes_recoverable_submitted(tmp_path):
    before = state()
    broker = Broker([snapshot(before)])

    def failing_submit(intent):
        broker.submissions.append(intent)
        raise TimeoutError("MT5 submission timeout")

    broker.submit = failing_submit
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    service = ControlledDemoExecutionService(executor, ledger, intent_id_factory=lambda: "intent-1", now=lambda: NOW)

    with pytest.raises(TimeoutError, match="MT5 submission timeout"):
        service.execute(OrderIntent("PETR4", "BUY", 0.01), internal_before=before,
                        internal_after_provider=lambda: before)

    record = ledger.get("intent-1")
    assert record.state == "SUBMITTED"
    assert record.error == "MT5 submission timeout"
    assert broker.submissions
