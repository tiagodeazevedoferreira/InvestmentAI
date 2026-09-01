from datetime import datetime, timezone

from backend.app.services.decision_observability import (
    DecisionEvidence,
    build_decision_record,
)
from backend.app.services.external_intelligence import Direction, FusedSignal


def fused():
    return FusedSignal(
        symbol="VALE3",
        direction=Direction.LONG,
        score=0.72,
        confidence=0.86,
        sources=("tradingview", "model"),
        blocked=False,
        reasons=(),
    )


def test_record_is_serializable_and_preserves_evidence():
    record = build_decision_record(
        decision_id="abc123",
        symbol="VALE3",
        fused=fused(),
        allowed=True,
        environment="paper",
        evidence=(
            DecisionEvidence("tradingview", "LONG", 1.0, "tv-event"),
            DecisionEvidence("model", "LONG", 0.72, "model-run"),
        ),
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    data = record.to_dict()
    assert data["decision_id"] == "abc123"
    assert data["direction"] == "LONG"
    assert data["allowed"] is True
    assert data["environment"] == "paper"
    assert len(data["sources"]) == 2
    assert data["sources"][0]["source"] == "tradingview"


def test_blocked_decision_keeps_risk_reasons():
    record = build_decision_record(
        decision_id="blocked-1",
        symbol="VALE3",
        fused=fused(),
        allowed=False,
        environment="paper",
        risk_reasons=("confidence threshold not met",),
    )
    assert record.allowed is False
    assert record.risk_reasons == ("confidence threshold not met",)
