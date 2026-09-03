from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..models import TradingViewWebhook


@dataclass(frozen=True)
class ReconciliationMatch:
    signal_id: str
    symbol: str
    paper_action: str
    tradingview_direction: str | None
    status: str
    paper_timestamp: str
    tradingview_timestamp: str | None
    delta_seconds: float | None


def _timestamp(value) -> datetime:
    ts = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _tv_direction(event: TradingViewWebhook) -> str:
    if event.ema_state == "bullish" and event.rsi_state != "overbought":
        return "LONG"
    if event.ema_state == "bearish" and event.rsi_state != "oversold":
        return "SHORT"
    return "NEUTRAL"


def _paper_direction(action: str) -> str:
    return {"BUY": "LONG", "SELL": "SHORT", "HOLD": "NEUTRAL"}.get(action.upper(), "UNKNOWN")


def reconcile_paper_decisions(
    decisions: list[dict],
    events: list[TradingViewWebhook],
    *,
    tolerance_seconds: float = 60.0,
) -> list[ReconciliationMatch]:
    """Compare paper decisions with TradingView evidence without execution authority.

    A match is based on normalized symbol and timestamp proximity. The result
    distinguishes missing evidence from a directional conflict; neither case
    is treated as an execution failure.
    """
    if tolerance_seconds < 0:
        raise ValueError("tolerance_seconds must be non-negative")

    normalized_events = [(event, _timestamp(event.bar_time)) for event in events]
    results: list[ReconciliationMatch] = []
    for decision in decisions:
        symbol = str(decision.get("symbol", "")).strip().upper().removesuffix(".SA")
        action = str(decision.get("action", "")).strip().upper()
        signal_id = str(decision.get("signal_id", ""))
        paper_ts = _timestamp(decision.get("bar_timestamp", decision.get("timestamp")))

        candidates = [
            (event, ts, abs((paper_ts - ts).total_seconds()))
            for event, ts in normalized_events
            if event.symbol.upper().removesuffix(".SA") == symbol
            and abs((paper_ts - ts).total_seconds()) <= tolerance_seconds
        ]
        if not candidates:
            results.append(ReconciliationMatch(
                signal_id, symbol, action, None, "paper_only",
                paper_ts.isoformat(), None, None,
            ))
            continue

        event, event_ts, delta = min(candidates, key=lambda item: item[2])
        paper_direction = _paper_direction(action)
        tv_direction = _tv_direction(event)
        status = "aligned" if paper_direction == tv_direction else "conflict"
        results.append(ReconciliationMatch(
            signal_id, symbol, action, tv_direction, status,
            paper_ts.isoformat(), event_ts.isoformat(), delta,
        ))

    matched_event_ids = set()
    for result in results:
        if result.tradingview_timestamp is not None:
            matched_event_ids.add((result.symbol, result.tradingview_timestamp))
    for event, event_ts in normalized_events:
        key = (event.symbol.upper().removesuffix(".SA"), event_ts.isoformat())
        if key not in matched_event_ids:
            results.append(ReconciliationMatch(
                "", event.symbol.upper().removesuffix(".SA"), "",
                _tv_direction(event), "tradingview_only", "",
                event_ts.isoformat(), None,
            ))
    return results
