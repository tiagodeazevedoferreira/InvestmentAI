import pandas as pd
import pytest

from app.services.auto_paper import decide


def series_for_rsi(value: float) -> pd.DataFrame:
    # Deterministic monotonic sequences produce unambiguous RSI regimes.
    if value < 30:
        close = [100 - i for i in range(40)]
    else:
        close = [60 + i for i in range(40)]
    return pd.DataFrame({"Close": close}, index=pd.date_range("2026-01-01", periods=40))


def test_decide_buy_when_oversold():
    d = decide(series_for_rsi(10), "PETR4")
    assert d.action == "BUY"
    assert d.quantity > 0
    assert d.signal_id


def test_decide_sell_when_overbought():
    d = decide(series_for_rsi(90), "PETR4")
    assert d.action == "SELL"
    assert d.quantity == 1


def test_rejects_missing_close():
    with pytest.raises(ValueError, match="Close"):
        decide(pd.DataFrame({"Open": [1, 2]}), "PETR4")
