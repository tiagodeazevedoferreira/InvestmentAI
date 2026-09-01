from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isclose

from .external_intelligence import Direction, ExternalSignal
from .tradingview import event_fingerprint
from ..models import TradingViewWebhook


@dataclass(frozen=True)
class ReconciliationResult:
    event_id: str
    symbol: str
    accepted: bool
    direction: Direction
    confidence: float
    reasons: tuple[str, ...]


def _direction(event: TradingViewWebhook) -> Direction:
    if event.ema_state == "bullish" and event.rsi_state != "overbought":
        return Direction.LONG
    if event.ema_state == "bearish" and event.rsi_state != "oversold":
        return Direction.SHORT
    return Direction.NEUTRAL


def reconcile(event: TradingViewWebhook, *, tolerance: float = 1e-6) -> ReconciliationResult:
    """Turn a confirmed TradingView event into an independent technical signal.

    The reconciliation layer is deliberately conservative: it only accepts a
    confirmed bar, internally consistent Bollinger bounds and finite numeric
    values. It never submits an order.
    """
    reasons: list[str] = []
    numeric = (event.close, event.ema_fast, event.ema_slow, event.rsi14,
               event.bb_upper, event.bb_basis, event.bb_lower, event.volume)
    if any(value != value or abs(value) == float("inf") for value in numeric):
        reasons.append("non-finite technical value")
    if not event.bar_confirmed:
        reasons.append("bar is not confirmed")
    if event.bb_upper < event.bb_basis or event.bb_basis < event.bb_lower:
        reasons.append("invalid Bollinger band ordering")
    if event.ema_state == "bullish" and not event.ema_fast > event.ema_slow:
        reasons.append("EMA state disagrees with EMA values")
    if event.ema_state == "bearish" and not event.ema_fast < event.ema_slow:
        reasons.append("EMA state disagrees with EMA values")
    if event.bb_state == "below_lower" and not event.close < event.bb_lower:
        reasons.append("BB state disagrees with close")
    if event.bb_state == "above_upper" and not event.close > event.bb_upper:
        reasons.append("BB state disagrees with close")
    if not 0 <= event.rsi14 <= 100:
        reasons.append("RSI outside valid range")

    direction = _direction(event)
    if direction is Direction.NEUTRAL:
        reasons.append("technical conditions do not form an actionable direction")

    accepted = not reasons
    confidence = 1.0 if accepted else 0.0
    return ReconciliationResult(
        event_id=event_fingerprint(event),
        symbol=event.symbol,
        accepted=accepted,
        direction=direction,
        confidence=confidence,
        reasons=tuple(reasons),
    )


def as_external_signal(event: TradingViewWebhook) -> ExternalSignal:
    result = reconcile(event)
    timestamp = event.bar_time
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return ExternalSignal(
        symbol=event.symbol,
        timestamp=timestamp.astimezone(timezone.utc),
        direction=result.direction,
        confidence=result.confidence if result.accepted else 0.0,
        entry=event.close,
        source="tradingview",
        source_version="InvestmentAI_Validator_v1",
        raw_reference=result.event_id,
        metadata={
            "exchange": event.exchange,
            "timeframe": event.timeframe,
            "rsi14": event.rsi14,
            "ema_fast": event.ema_fast,
            "ema_slow": event.ema_slow,
            "bb_upper": event.bb_upper,
            "bb_basis": event.bb_basis,
            "bb_lower": event.bb_lower,
            "volume": event.volume,
        },
    )
