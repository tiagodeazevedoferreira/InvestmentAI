from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.services.scheduler_demo_execution import (
    SchedulerDemoExecutionAdapter,
    SchedulerDemoExecutionBlocked,
)
from app.services.scheduler_demo_bridge import DemoPromotionPlan


@dataclass
class FakeExecutionService:
    calls: list

    def execute(self, intent, *, internal_before, internal_after_provider):
        self.calls.append(
            {
                "intent": intent,
                "internal_before": internal_before,
                "internal_after_provider": internal_after_provider,
            }
        )
        return "controlled-result"


def ready_plan():
    return DemoPromotionPlan(
        status="ready",
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        reference_price=1.1596,
        signal_id="signal-1",
        intent=SimpleNamespace(
            symbol="EURUSD",
            side="BUY",
            quantity=0.01,
            limit_price=1.1596,
        ),
    )


def test_scheduler_handoff_requires_explicit_independent_authorization():
    service = FakeExecutionService([])
    adapter = SchedulerDemoExecutionAdapter(service)

    with pytest.raises(SchedulerDemoExecutionBlocked, match="explicit independent authorization"):
        adapter.execute(
            ready_plan(),
            internal_before={"cash": 52000.0},
            internal_after_provider=lambda: {"cash": 52000.0},
        )

    assert service.calls == []


def test_scheduler_handoff_rejects_non_ready_plan_even_when_authorized():
    service = FakeExecutionService([])
    adapter = SchedulerDemoExecutionAdapter(service)
    blocked_plan = DemoPromotionPlan(
        status="blocked",
        symbol="EURUSD",
        reason="risk rejected",
    )

    with pytest.raises(SchedulerDemoExecutionBlocked, match="not ready"):
        adapter.execute(
            blocked_plan,
            execution_authorized=True,
            internal_before={"cash": 52000.0},
            internal_after_provider=lambda: {"cash": 52000.0},
        )

    assert service.calls == []


def test_scheduler_handoff_delegates_only_after_explicit_authorization():
    service = FakeExecutionService([])
    adapter = SchedulerDemoExecutionAdapter(service)
    before = {"cash": 52000.0}
    after_provider = lambda: {"cash": 52000.0}

    result = adapter.execute(
        ready_plan(),
        execution_authorized=True,
        internal_before=before,
        internal_after_provider=after_provider,
    )

    assert result == "controlled-result"
    assert len(service.calls) == 1
    assert service.calls[0]["intent"].symbol == "EURUSD"
    assert service.calls[0]["intent"].side == "BUY"
    assert service.calls[0]["intent"].quantity == 0.01
    assert service.calls[0]["internal_before"] == before
    assert service.calls[0]["internal_after_provider"] is after_provider
