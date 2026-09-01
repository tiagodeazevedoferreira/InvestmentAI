from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .external_intelligence import ExternalSignal, FusedSignal, RiskGate, SignalFusion
from .tradingview_reconciliation import reconcile
from ..models import TradingViewWebhook


@dataclass(frozen=True)
class PipelineDecision:
    fused: FusedSignal
    allowed: bool
    risk_reasons: tuple[str, ...]


def fuse_with_tradingview(
    tradingview_event: TradingViewWebhook,
    other_signals: list[ExternalSignal] | None = None,
    *,
    weights: dict[str, float] | None = None,
    min_confidence: float = 0.60,
    min_sources: int = 2,
    environment: str = "paper",
) -> PipelineDecision:
    """Add TradingView as independent evidence and run the existing gates.

    This function produces a decision only. It has no broker dependency and
    cannot place, modify, or cancel an order.
    """
    reconciliation = reconcile(tradingview_event)
    timestamp = tradingview_event.bar_time
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    tv_signal = ExternalSignal(
        symbol=tradingview_event.symbol,
        timestamp=timestamp.astimezone(timezone.utc),
        direction=reconciliation.direction,
        confidence=reconciliation.confidence if reconciliation.accepted else 0.0,
        entry=tradingview_event.close,
        source="tradingview",
        source_version="InvestmentAI_Validator_v1",
        raw_reference=reconciliation.event_id,
        metadata={"reconciliation_reasons": reconciliation.reasons},
    )
    signals = [tv_signal, *(other_signals or [])]
    fused = SignalFusion(weights=weights, min_confidence=min_confidence).fuse(signals)
    age = max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds())
    allowed, reasons = RiskGate(
        min_confidence=min_confidence,
        min_sources=min_sources,
    ).evaluate(fused, signal_age_seconds=age, environment=environment)
    return PipelineDecision(fused=fused, allowed=allowed, risk_reasons=reasons)
