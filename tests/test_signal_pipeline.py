from backend.app.models import TradingViewWebhook
from backend.app.services.external_intelligence import Direction, ExternalSignal
from backend.app.services.signal_pipeline import fuse_with_tradingview


def tv_event():
    return TradingViewWebhook.model_validate({
        "source": "tradingview", "symbol": "VALE3", "exchange": "BMFBOVESPA",
        "timeframe": "D", "bar_time": "2026-09-01T00:00:00Z", "close": 100,
        "ema_fast": 101, "ema_slow": 99, "rsi14": 55, "bb_upper": 105,
        "bb_basis": 100, "bb_lower": 95, "volume": 1000000,
        "ema_state": "bullish", "rsi_state": "neutral", "bb_state": "inside",
        "bar_confirmed": True,
    })


def signal(direction, confidence, source):
    return ExternalSignal(symbol="VALE3", timestamp=tv_event().bar_time,
                          direction=direction, confidence=confidence, source=source)


def test_tradingview_and_independent_bullish_signal_pass_fusion():
    result = fuse_with_tradingview(tv_event(), [signal(Direction.LONG, 0.9, "model")], min_sources=2)
    assert result.fused.direction is Direction.LONG
    assert result.allowed is True
    assert "tradingview" in result.fused.sources
    assert "model" in result.fused.sources


def test_conflicting_sources_are_fused_instead_of_tradingview_overriding():
    result = fuse_with_tradingview(tv_event(), [signal(Direction.SHORT, 1.0, "model")], min_sources=2)
    assert result.fused.direction is Direction.SHORT
    assert result.allowed is False
    assert "confidence threshold not met" in result.risk_reasons or "fused confidence below threshold" in result.risk_reasons


def test_single_tradingview_source_is_blocked_by_independent_evidence_gate():
    result = fuse_with_tradingview(tv_event(), [], min_sources=2)
    assert result.allowed is False
    assert "independent evidence threshold not met" in result.risk_reasons
