import pandas as pd
import pytest

from backend.app.services.openbb_market_data import OpenBBMarketDataProvider


def test_normalize_b3_symbol():
    provider = OpenBBMarketDataProvider()
    assert provider.normalize_symbol("VALE3") == "VALE3.SA"
    assert provider.normalize_symbol("petr4.sa") == "PETR4.SA"


def test_quality_gate_accepts_clean_ohlcv():
    index = pd.date_range("2026-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "open": [1, 2, 3],
            "high": [2, 3, 4],
            "low": [0, 1, 2],
            "close": [1.5, 2.5, 3.5],
            "volume": [100, 200, 300],
        },
        index=index,
    )
    quality = OpenBBMarketDataProvider.quality("VALE3", df)
    assert quality.valid


def test_quality_gate_rejects_duplicate_timestamp():
    index = pd.to_datetime(["2026-01-01", "2026-01-01"])
    df = pd.DataFrame(
        {
            "open": [1, 2],
            "high": [2, 3],
            "low": [0, 1],
            "close": [1.5, 2.5],
            "volume": [100, 200],
        },
        index=index,
    )
    quality = OpenBBMarketDataProvider.quality("VALE3", df)
    assert not quality.valid
    assert quality.duplicate_timestamps == 1


def test_empty_symbol_is_rejected():
    with pytest.raises(ValueError):
        OpenBBMarketDataProvider.normalize_symbol(" ")
