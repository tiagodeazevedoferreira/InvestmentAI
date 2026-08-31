from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import pandas as pd


class MarketDataProvider(Protocol):
    def history(self, symbol: str, period: str = "5y") -> pd.DataFrame: ...
    def fundamentals(self, symbol: str) -> dict: ...


@dataclass
class YahooProvider:
    def history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        from .market_data import download_history
        return download_history(symbol, period)

    def fundamentals(self, symbol: str) -> dict:
        import yfinance as yf
        ticker = yf.Ticker(symbol.strip().upper())
        info = ticker.info or {}
        return {k: info.get(k) for k in (
            "marketCap", "enterpriseValue", "trailingPE", "priceToBook",
            "enterpriseToEbitda", "returnOnEquity", "returnOnAssets",
            "dividendYield", "totalRevenue", "netIncomeToCommon", "ebitda",
            "totalStockholderEquity", "totalDebt", "freeCashflow", "currentPrice"
        )}


@dataclass
class OpenBBProvider:
    """OpenBB-first provider. Falls back only when explicitly requested by caller."""
    def history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        try:
            from openbb import obb
            result = obb.equity.price.historical(symbol=symbol.upper(), provider="yfinance")
            df = result.to_dataframe()
            if df.empty:
                raise ValueError(f"OpenBB returned no history for {symbol}")
            if "date" in df.columns:
                df = df.set_index("date")
            return df.rename(columns={c: c.title() for c in df.columns})
        except ImportError as exc:
            raise RuntimeError("OpenBB is not installed") from exc
        except Exception as exc:
            raise RuntimeError(f"OpenBB history error for {symbol}: {exc}") from exc

    def fundamentals(self, symbol: str) -> dict:
        try:
            from openbb import obb
            result = obb.equity.fundamental.metrics(symbol=symbol.upper(), provider="yfinance")
            df = result.to_dataframe()
            if df.empty:
                raise ValueError(f"OpenBB returned no fundamentals for {symbol}")
            return df.tail(1).reset_index().to_dict(orient="records")[0]
        except ImportError as exc:
            raise RuntimeError("OpenBB is not installed") from exc
        except Exception as exc:
            raise RuntimeError(f"OpenBB fundamentals error for {symbol}: {exc}") from exc


def get_provider(name: str = "openbb") -> MarketDataProvider:
    if name.lower() == "openbb":
        return OpenBBProvider()
    if name.lower() == "yahoo":
        return YahooProvider()
    raise ValueError(f"Unsupported market data provider: {name}")
