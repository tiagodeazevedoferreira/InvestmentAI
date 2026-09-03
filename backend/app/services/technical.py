import numpy as np
import pandas as pd

REQUIRED_OHLCV = {"Open", "High", "Low", "Close", "Volume"}

def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("No market data available")
    missing = REQUIRED_OHLCV - set(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    out = df.copy().sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out

def indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = validate_ohlcv(df)
    close = out["Close"].astype(float)
    out["EMA9"] = close.ewm(span=9, adjust=False).mean()
    out["EMA21"] = close.ewm(span=21, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    # A strictly rising series has zero losses, so its RSI is 100 rather than NA.
    rsi = rsi.mask((loss == 0) & (gain > 0), 100.0)
    # A flat series has neither gains nor losses; keep it neutral.
    rsi = rsi.mask((loss == 0) & (gain == 0), 50.0)
    out["RSI14"] = rsi
    ma = close.rolling(20).mean()
    std = close.rolling(20).std(ddof=0)
    out["BB_MIDDLE"] = ma
    out["BB_UPPER"] = ma + 2 * std
    out["BB_LOWER"] = ma - 2 * std
    return out

def rsi_signal(row: pd.Series) -> str:
    rsi = row.get("RSI14")
    if pd.isna(rsi):
        return "HOLD"
    if rsi < 30:
        return "BUY"
    if rsi > 70:
        return "SELL"
    return "HOLD"
