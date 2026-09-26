from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.controlled_demo_execution import ControlledDemoExecutionService
from app.services.demo_ledger import DemoOrderLedger
from app.services.mt5_demo_broker import _broker_comment, _correlation_from_comment
from app.services.order_manager import OrderIntent


class FakePreflight:
    def validate(self, intent, *, environment):
        assert environment == "demo"
        return intent

    def validate_state(self, state):
        assert isinstance(state, dict)


class AmbiguousSubmitExecutor:
    def __init__(self) -> None:
        self.preflight = FakePreflight()
        self.submit_calls = 0
        self.last_intent = None

    def execute(self, intent, *, internal_before, internal_after_provider,
                on_authorized=None, on_submitted=None):
        self.last_intent = intent
        if on_authorized is not None:
            on_authorized()
        self.submit_calls += 1
        raise ConnectionError("broker accepted request but response was lost")


def test_interrupted_submission_persists_correlation_and_recovers_without_retry(tmp_path: Path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite")
    executor = AmbiguousSubmitExecutor()
    service = ControlledDemoExecutionService(
        executor,
        ledger,
        intent_id_factory=lambda: "intent-001",
        correlation_id_factory=lambda: "corr-001",
    )

    with pytest.raises(ConnectionError, match="response was lost"):
        service.execute(
            OrderIntent(symbol="EURUSD", side="BUY", quantity=0.01),
            internal_before={"cash": 100_000},
            internal_after_provider=lambda: {"cash": 100_000},
        )

    pending = ledger.get("intent-001")
    assert pending.state == "SUBMITTED"
    assert pending.correlation_id == "corr-001"
    assert executor.submit_calls == 1

    evidence = {
        "executions": [
            {
                "execution_id": "deal-9001",
                "order_id": "order-9001",
                "symbol": "EURUSD",
                "side": "BUY",
                "quantity": 0.01,
                "correlation_id": "corr-001",
            }
        ]
    }
    recovered = service.recover_pending(lambda record: evidence)

    assert recovered[0].state == "FILLED"
    assert recovered[0].deal_id == "deal-9001"
    assert recovered[0].order_id == "order-9001"
    assert recovered[0].execution == evidence["executions"][0]
    assert executor.submit_calls == 1


def test_recovery_rejects_same_correlation_with_wrong_order_shape(tmp_path: Path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite")
    ledger.create(
        "intent-002", "EURUSD", "BUY", 0.01,
        correlation_id="corr-002",
    )
    ledger.transition("intent-002", "AUTHORIZED")
    ledger.transition("intent-002", "SUBMITTED")

    service = ControlledDemoExecutionService(
        AmbiguousSubmitExecutor(),
        ledger,
        intent_id_factory=lambda: "unused",
        correlation_id_factory=lambda: "unused",
    )

    evidence = {
        "executions": [
            {
                "execution_id": "deal-wrong",
                "order_id": "order-wrong",
                "symbol": "EURUSD",
                "side": "SELL",
                "quantity": 0.01,
                "correlation_id": "corr-002",
            }
        ]
    }

    recovered = service.recover_pending(lambda record: evidence)

    assert recovered[0].state == "SUBMITTED"
    assert recovered[0].deal_id is None


def test_mt5_correlation_comment_is_bounded_and_round_trips():
    correlation = "1234567890abcdef1234"
    comment = _broker_comment(correlation)

    assert len(comment) <= 31
    assert comment == "IAI:" + correlation
    assert _correlation_from_comment(comment) == correlation


def test_mt5_empty_correlation_preserves_legacy_comment():
    assert _broker_comment(None) == "InvestmentAI-DEMO"
    assert _correlation_from_comment("InvestmentAI-DEMO") is None
