from types import SimpleNamespace

import pandas as pd

from app.services.paper_scheduler import run_symbol
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


def test_run_symbol_exposes_demo_plan_without_broker_submission(monkeypatch):
    class FakeProvider:
        def history(self, symbol, period="3mo"):
            assert symbol == "PETR4.SA"
            return pd.DataFrame(
                {"Close": [42.0]},
                index=pd.to_datetime(["2026-09-11T20:00:00+00:00"]),
            )

    class FakeSettings:
        paper_max_order_notional = 1000.0

    class FakeStore:
        settings = FakeSettings()

        def get(self):
            return {"cash": 52000.0}

        def save(self):
            raise AssertionError("paper execution should not save an account in this dry-run")

    class FakeLedger:
        def claim(self, signal_id, **kwargs):
            return True, {"signal_id": signal_id, **kwargs}

        def complete(self, *args, **kwargs):
            return None

    calls = []

    def fake_evaluate(*args, **kwargs):
        calls.append(kwargs)
        return {
            "decision": {
                "action": "BUY",
                "quantity": 2.0,
                "reference_price": 42.0,
                "risk_allowed": True,
                "reason": "dry-run decision",
            },
            "executed": False,
            "order": None,
        }

    monkeypatch.setattr("app.services.paper_scheduler.evaluate_paper_signal", fake_evaluate)

    result = run_symbol(
        FakeProvider(),
        FakeStore(),
        FakeLedger(),
        "PETR4",
        execute=False,
        demo_bridge=SchedulerDemoBridge(enabled=True, symbol_map={"PETR4": "PETR4"}),
    )

    assert len(calls) == 2
    assert result.status == "decided"
    assert result.executed is False
    assert result.demo_plan is not None
    assert result.demo_plan.status == "ready"
    assert result.demo_plan.intent is not None
    assert result.demo_plan.intent.symbol == "PETR4"
    assert result.demo_plan.intent.side == "BUY"
    assert result.demo_plan.intent.quantity == 2.0
    assert "submission remains disabled" in result.demo_plan.reason
