from datetime import datetime, timedelta, timezone

import pytest

from app.services.demo_authorization import DemoAuthorizationGate
from app.services.demo_execution import AuthorizedDemoExecutor, DemoExecutionBlocked
from app.services.operational_kill_switch import OperationalKillSwitch
from app.services.order_manager import OrderIntent


NOW = datetime(2026, 9, 4, 17, 0, tzinfo=timezone.utc)


def _state(cash=1000.0, quantity=10, executions=None):
    return {
        "cash": cash,
        "positions": {"PETR4": {"quantity": quantity}},
        "open_orders": [],
        "executions": executions or [],
    }


class FakeDemoBroker:
    environment = "demo"

    def __init__(self, snapshots):
        self.snapshots = iter(snapshots)
        self.submissions = []

    def reconciliation_snapshot(self, date_from, date_to):
        return next(self.snapshots)

    def submit(self, intent):
        self.submissions.append(intent)
        return {"order_id": "o-demo-1", "deal_id": "e-demo-1", "status": "accepted", "environment": "demo"}


def _snapshot(state, captured_at=NOW):
    return {**state, "captured_at": captured_at.isoformat()}


def test_executes_only_after_pre_authorization_and_post_reconciliation():
    post_state = _state(cash=900.0, quantity=20, executions=[{"execution_id": "e-demo-1"}])
    broker = FakeDemoBroker([_snapshot(_state()), _snapshot(post_state)])
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    executor = AuthorizedDemoExecutor(broker, gate, now=lambda: NOW)

    result = executor.execute(
        OrderIntent(symbol="PETR4", side="BUY", quantity=10),
        internal_before=_state(),
        internal_after=post_state,
    )

    assert result.authorization.allowed is True
    assert result.post_reconciliation.healthy is True
    assert len(broker.submissions) == 1


def test_blocks_when_pre_reconciliation_is_unhealthy():
    external = _snapshot(_state(quantity=11))
    broker = FakeDemoBroker([external])
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    executor = AuthorizedDemoExecutor(broker, gate, now=lambda: NOW)

    with pytest.raises(PermissionError, match="position quantity mismatch: PETR4"):
        executor.execute(
            OrderIntent(symbol="PETR4", side="BUY", quantity=1),
            internal_before=_state(),
            internal_after=_state(),
        )
    assert broker.submissions == []


def test_blocks_non_demo_broker_before_snapshot():
    broker = FakeDemoBroker([_snapshot(_state())])
    broker.environment = "live"
    executor = AuthorizedDemoExecutor(broker, DemoAuthorizationGate(OperationalKillSwitch()), now=lambda: NOW)

    with pytest.raises(DemoExecutionBlocked, match="environment=demo"):
        executor.execute(OrderIntent("PETR4", "BUY", 1), internal_before=_state(), internal_after=_state())
    assert broker.submissions == []


def test_blocks_when_post_execution_reconciliation_fails():
    broker = FakeDemoBroker([_snapshot(_state()), _snapshot(_state(cash=899.0, quantity=20))])
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    executor = AuthorizedDemoExecutor(broker, gate, now=lambda: NOW)

    with pytest.raises(DemoExecutionBlocked, match="post-execution reconciliation failed"):
        executor.execute(
            OrderIntent("PETR4", "BUY", 10),
            internal_before=_state(),
            internal_after=_state(cash=900.0, quantity=20),
        )
    assert len(broker.submissions) == 1


def test_stale_pre_snapshot_blocks_before_submit():
    stale = NOW - timedelta(seconds=121)
    broker = FakeDemoBroker([_snapshot(_state(), stale)])
    gate = DemoAuthorizationGate(OperationalKillSwitch(), max_evidence_age_seconds=120)
    executor = AuthorizedDemoExecutor(broker, gate, now=lambda: NOW)

    with pytest.raises(PermissionError, match="reconciliation evidence is stale"):
        executor.execute(OrderIntent("PETR4", "BUY", 1), internal_before=_state(), internal_after=_state())
    assert broker.submissions == []
