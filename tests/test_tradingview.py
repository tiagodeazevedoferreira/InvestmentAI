from datetime import datetime, timezone

from app.services.tradingview import event_fingerprint, normalize_tradingview_payload, verify_webhook_secret


PAYLOAD = {
    "source": "tradingview",
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
    "volume": 1000000,
    "ema_state": "bullish",
    "rsi_state": "neutral",
    "bb_state": "inside",
    "bar_confirmed": True,
}


def test_webhook_payload_normalizes_and_fingerprints():
    event = normalize_tradingview_payload(PAYLOAD)
    assert event.symbol == "VALE3"
    assert event.exchange == "BMFBOVESPA"
    assert event.rsi14 == 62.5
    assert event.bar_time == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert len(event_fingerprint(event)) == 64


def test_webhook_secret_uses_constant_time_comparison():
    assert verify_webhook_secret("secret", "secret") is True
    assert verify_webhook_secret("wrong", "secret") is False
    assert verify_webhook_secret(None, "secret") is False
    assert verify_webhook_secret("secret", None) is False
