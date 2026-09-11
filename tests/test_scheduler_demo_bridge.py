from types import SimpleNamespace

from app.services.scheduler_demo_bridge import SchedulerDemoBridge


def scheduler_result(**overrides):
    values = {
        "symbol": "EURUSD",
        "status": "decided",
        "signal_id": "signal-1",
        "action": "BUY",
        "quantity": 0.01,
        "reference_price": 1.1596,
        "risk_allowed": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_bridge_is_disabled_by_default():
    plan = SchedulerDemoBridge().plan(scheduler_result())

    assert plan.status == "disabled"
    assert plan.intent is None
    assert "disabled by default" in plan.reason


def test_enabled_bridge_requires_explicit_symbol_mapping():
    plan = SchedulerDemoBridge(enabled=True).plan(scheduler_result())

    assert plan.status == "blocked"
    assert plan.intent is None
    assert "symbol mapping" in plan.reason


def test_enabled_bridge_builds_intent_without_submitting():
    bridge = SchedulerDemoBridge(enabled=True, symbol_map={"EURUSD": "EURUSD"})

    plan = bridge.plan(scheduler_result())

    assert plan.status == "ready"
    assert plan.intent is not None
    assert plan.intent.symbol == "EURUSD"
    assert plan.intent.side == "BUY"
    assert plan.intent.quantity == 0.01
    assert plan.intent.limit_price == 1.1596
    assert "submission remains disabled" in plan.reason


def test_bridge_blocks_non_decision_and_risk_rejected_results():
    bridge = SchedulerDemoBridge(enabled=True, symbol_map={"EURUSD": "EURUSD"})

    duplicate = bridge.plan(scheduler_result(status="duplicate_skipped"))
    risk_blocked = bridge.plan(scheduler_result(risk_allowed=False, quantity=0))

    assert duplicate.status == "blocked"
    assert risk_blocked.status == "blocked"
    assert duplicate.intent is None
    assert risk_blocked.intent is None
