from datetime import datetime, timedelta, timezone

import pytest

from app.services.demo_authorization import DemoAuthorizationBlocked, DemoAuthorizationGate
from app.services.operational_kill_switch import OperationalKillSwitch


def _state():
    return {
        "cash": 1000.0,
        "positions": {"PETR4": {"quantity": 10}},
        "open_orders": [{"order_id": "o1"}],
        "executions": [{"execution_id": "e1"}],
    }


def test_authorizes_healthy_demo_state():
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    result = gate.authorize(
        environment="demo",
        internal=_state(),
        external=_state(),
        evidence_timestamp=datetime.now(timezone.utc),
    )
    assert result.allowed is True
    assert result.reconciliation is not None
    assert result.reconciliation.healthy is True


def test_blocks_non_demo_environment():
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    result = gate.authorize(environment="live", internal=_state(), external=_state())
    assert result.allowed is False
    assert "environment=demo" in result.reasons[0]
    assert result.reconciliation is None


def test_blocks_active_kill_switch_before_reconciliation():
    switch = OperationalKillSwitch()
    switch.activate("manual stop", operator="operator")
    gate = DemoAuthorizationGate(switch)
    result = gate.authorize(environment="demo", internal=_state(), external={})
    assert result.allowed is False
    assert result.reasons == ("kill switch is active",)
    assert result.reconciliation is None


def test_blocks_reconciliation_mismatch():
    external = _state()
    external["positions"] = {"PETR4": {"quantity": 11}}
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    result = gate.authorize(environment="demo", internal=_state(), external=external)
    assert result.allowed is False
    assert "position quantity mismatch: PETR4" in result.reasons


def test_blocks_stale_external_evidence():
    gate = DemoAuthorizationGate(OperationalKillSwitch(), max_evidence_age_seconds=120)
    result = gate.authorize(
        environment="demo",
        internal=_state(),
        external=_state(),
        evidence_timestamp=datetime.now(timezone.utc) - timedelta(seconds=121),
    )
    assert result.allowed is False
    assert "reconciliation evidence is stale" in result.reasons


def test_require_authorized_raises_when_blocked():
    gate = DemoAuthorizationGate(OperationalKillSwitch())
    with pytest.raises(DemoAuthorizationBlocked, match="cash mismatch"):
        gate.require_authorized(
            environment="demo",
            internal=_state(),
            external={**_state(), "cash": 999.0},
        )
