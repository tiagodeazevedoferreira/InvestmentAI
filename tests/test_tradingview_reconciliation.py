from backend.app.models import TradingViewWebhook
from backend.app.services.tradingview_reconciliation import as_external_signal, reconcile


def event(**overrides):
    payload = {
        "source": "tradingview", "symbol": "VALE3", "exchange": "BMFBOVESPA",
        "timeframe": "D", "bar_time": "2026-09-01T00:00:00Z", "close": 100,
        "ema_fast": 99, "ema_slow": 98, "rsi14": 62, "bb_upper": 105,
        "bb_basis": 100, "bb_lower": 95, "volume": 1000000,
        "ema_state": "bullish", "rsi_state": "neutral", "bb_state": "inside",
        "bar_confirmed": True,
    }
    payload.update(overrides)
    return TradingViewWebhook.model_validate(payload)


def test_reconcile_accepts_consistent_confirmed_bullish_event():
    result = reconcile(event())
    assert result.accepted is True
    assert result.direction.value == "LONG"
    assert result.confidence == 1.0


def test_reconcile_rejects_unconfirmed_event():
    result = reconcile(event(bar_confirmed=False))
    assert result.accepted is False
    assert "bar is not confirmed" in result.reasons


def test_reconcile_rejects_inconsistent_ema_state():
    result = reconcile(event(ema_state="bearish"))
    assert result.accepted is False
    assert "EMA state disagrees with EMA values" in result.reasons


def test_external_signal_is_read_only_and_provider_tagged():
    signal = as_external_signal(event())
    assert signal.source == "tradingview"
    assert signal.direction.value == "LONG"
    assert signal.entry == 100
