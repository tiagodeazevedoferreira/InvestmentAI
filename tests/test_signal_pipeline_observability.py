from backend.app.models import TradingViewWebhook
from backend.app.services.external_intelligence import Direction, ExternalSignal
from backend.app.services.signal_pipeline import fuse_with_tradingview


def test_pipeline_attaches_all_signal_evidence_to_audit_record():
    event = TradingViewWebhook.model_validate({
        "source": "tradingview", "symbol": "VALE3", "exchange": "BMFBOVESPA",
        "timeframe": "D", "bar_time": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "close": 100, "ema_fast": 101, "ema_slow": 99, "rsi14": 55,
        "bb_upper": 105, "bb_basis": 100, "bb_lower": 95, "volume": 1000000,
        "ema_state": "bullish", "rsi_state": "neutral", "bb_state": "inside",
        "bar_confirmed": True,
    })
    model = ExternalSignal(symbol="VALE3", timestamp=event.bar_time, direction=Direction.LONG,
                            confidence=0.9, source="model", raw_reference="model-run-1")
    result = fuse_with_tradingview(event, [model], min_sources=2)
    assert result.audit.symbol == "VALE3"
    assert result.audit.direction == "LONG"
    assert result.audit.allowed is True
    assert {item.source for item in result.audit.sources} == {"tradingview", "model"}
