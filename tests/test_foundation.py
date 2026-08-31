import pandas as pd
from backend.app.services.technical import indicators

def test_indicators():
    idx = pd.date_range("2025-01-01", periods=40, freq="D")
    close = pd.Series(range(100, 140), index=idx, dtype=float)
    df = pd.DataFrame({"Open": close, "High": close+1, "Low": close-1, "Close": close, "Volume": 1000}, index=idx)
    out = indicators(df)
    assert "EMA9" in out and "EMA21" in out and "RSI14" in out
    assert out["EMA9"].notna().all()

def test_empty_data_rejected():
    try:
        indicators(pd.DataFrame())
    except ValueError as exc:
        assert "No market data" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
