from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.operational_kill_switch import OperationalKillSwitch
from backend.app.services.operational_reconciliation import OperationalReconciler


def test_kill_switch_is_clear_by_default():
    switch = OperationalKillSwitch()
    assert switch.allows_operation()


def test_kill_switch_activation_blocks_and_records_reason():
    switch = OperationalKillSwitch()
    state = switch.activate("manual emergency stop", operator="operator-1")
    assert state.active
    assert state.reason == "manual emergency stop"
    assert not switch.allows_operation()
    with pytest.raises(PermissionError, match="manual emergency stop"):
        switch.require_clear()


def test_kill_switch_reset_requires_operator():
    switch = OperationalKillSwitch()
    switch.activate("test")
    state = switch.reset(operator="operator-1")
    assert not state.active
    assert switch.allows_operation()


def test_kill_switch_requires_reason_and_operator():
    switch = OperationalKillSwitch()
    with pytest.raises(ValueError):
        switch.activate("", operator="operator-1")
    with pytest.raises(ValueError):
        switch.activate("test", operator="")


def _snapshot():
    return {
        "cash": 1000.00,
        "positions": {"PETR4": {"quantity": 10}},
        "open_orders": [{"order_id": "o1"}],
        "executions": [{"execution_id": "e1"}],
    }


def test_reconciliation_healthy_when_states_match():
    snapshot = _snapshot()
    result = OperationalReconciler().evaluate(
        snapshot,
        snapshot,
        evidence_timestamp=datetime.now(timezone.utc),
    )
    assert result.healthy
    assert result.status == "healthy"
    assert result.reasons == ()


def test_reconciliation_blocks_cash_and_position_mismatch():
    internal = _snapshot()
    external = _snapshot()
    external["cash"] = 999.0
    external["positions"]["PETR4"]["quantity"] = 9
    result = OperationalReconciler().evaluate(internal, external)
    assert result.status == "blocked"
    assert "cash mismatch" in result.reasons
    assert "position quantity mismatch: PETR4" in result.reasons


def test_reconciliation_blocks_open_order_mismatch():
    internal = _snapshot()
    external = _snapshot()
    external["open_orders"] = []
    result = OperationalReconciler().evaluate(internal, external)
    assert result.status == "blocked"
    assert "open order set mismatch" in result.reasons


def test_reconciliation_blocks_execution_mismatch():
    internal = _snapshot()
    external = _snapshot()
    external["executions"] = []
    result = OperationalReconciler().evaluate(internal, external)
    assert result.status == "blocked"
    assert "internal executions missing externally" in result.reasons


def test_reconciliation_blocks_stale_evidence():
    snapshot = _snapshot()
    old = datetime.now(timezone.utc) - timedelta(minutes=3)
    result = OperationalReconciler().evaluate(
        snapshot,
        snapshot,
        evidence_timestamp=old,
        max_evidence_age_seconds=120,
    )
    assert result.status == "blocked"
    assert "reconciliation evidence is stale" in result.reasons


def test_reconciliation_rejects_future_evidence():
    snapshot = _snapshot()
    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    result = OperationalReconciler().evaluate(snapshot, snapshot, evidence_timestamp=future)
    assert result.status == "blocked"
    assert "reconciliation evidence timestamp is in the future" in result.reasons
