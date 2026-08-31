import pandas as pd

def download_history(symbol: str, period: str = "5y") -> pd.DataFrame:
    if not symbol or not symbol.strip():
        raise ValueError("Symbol is required")
    try:
        import yfinance as yf
        df = yf.download(symbol.strip().upper(), period=period, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            raise ValueError(f"No historical data returned for {symbol}")
        return df
    except ImportError as exc:
        raise RuntimeError("yfinance is not installed") from exc
    except Exception as exc:
        raise RuntimeError(f"Market data provider error for {symbol}: {exc}") from exc
