from datetime import datetime, timezone

import pandas as pd

from backend.app.models import TradingViewWebhook
from backend.app.services.paper_regime import classify_regime
from backend.app.services.paper_tradingview_reconciliation import reconcile_paper_decisions


def _event(**overrides):
    payload = {
        "symbol": "VALE3",
        "exchange": "BMFBOVESPA",
        "timeframe": "1D",
        "bar_time": "2026-09-01T00:00:00Z",
        "close": 100.0,
        "ema_fast": 99.0,
        "ema_slow": 98.0,
        "rsi14": 62.5,
        "bb_upper": 105.0,
        "bb_basis": 100.0,
        "bb_lower": 95.0,
        "volume": 1_000_000,
        "ema_state": "bullish",
        "rsi_state": "neutral",
        "bb_state": "inside",
        "bar_confirmed": True,
    }
    payload.update(overrides)
    return TradingViewWebhook(**payload)


def test_regime_uses_only_bars_at_or_before_decision():
    idx = pd.date_range("2026-01-01", periods=23, freq="D", tz="UTC")
    closes = [100 + i * 0.1 for i in range(23)]
    frame = pd.DataFrame({"Close": closes}, index=idx)
    baseline = classify_regime(frame, decision_timestamp=idx[21])
    mutated = frame.copy()
    mutated.loc[idx[22], "Close"] = 10_000
    after_future_change = classify_regime(mutated, decision_timestamp=idx[21])
    assert baseline == after_future_change
    assert baseline.label == "low"


def test_regime_requires_window_plus_one_closes():
    frame = pd.DataFrame({"Close": [100.0] * 20}, index=pd.date_range("2026-01-01", periods=20, tz="UTC"))
    result = classify_regime(frame)
    assert result.label == "insufficient_history"
    assert result.realized_volatility is None


def test_reconciliation_distinguishes_aligned_conflict_and_missing():
    decisions = [
        {"signal_id": "a", "symbol": "VALE3", "action": "BUY", "bar_timestamp": "2026-09-01T00:00:00Z"},
        {"signal_id": "b", "symbol": "VALE3", "action": "SELL", "bar_timestamp": "2026-09-01T00:00:00Z"},
        {"signal_id": "c", "symbol": "PETR4", "action": "BUY", "bar_timestamp": "2026-09-01T00:00:00Z"},
    ]
    results = reconcile_paper_decisions(decisions, [_event()])
    statuses = {item.signal_id: item.status for item in results if item.signal_id}
    assert statuses["a"] == "aligned"
    assert statuses["b"] == "conflict"
    assert statuses["c"] == "paper_only"


def test_reconciliation_reports_tradingview_only_evidence():
    results = reconcile_paper_decisions([], [_event()])
    assert len(results) == 1
    assert results[0].status == "tradingview_only"
    assert results[0].tradingview_direction == "LONG"


def test_timestamp_tolerance_is_explicit():
    event = _event(bar_time="2026-09-01T00:00:30Z")
    decisions = [{"signal_id": "a", "symbol": "VALE3", "action": "BUY", "bar_timestamp": "2026-09-01T00:00:00Z"}]
    result = reconcile_paper_decisions(decisions, [event], tolerance_seconds=60)[0]
    assert result.status == "aligned"
    assert result.delta_seconds == 30.0
