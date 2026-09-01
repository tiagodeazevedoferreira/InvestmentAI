from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


B3_SYMBOLS = {"PETR4", "VALE3", "ITUB4"}


@dataclass(frozen=True)
class MarketDataQuality:
    symbol: str
    rows: int
    required_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    duplicate_timestamps: int
    null_required_values: int
    monotonic_timestamps: bool

    @property
    def valid(self) -> bool:
        return (
            self.rows > 0
            and not self.missing_columns
            and self.duplicate_timestamps == 0
            and self.null_required_values == 0
            and self.monotonic_timestamps
        )


class OpenBBMarketDataProvider:
    """Market-data adapter using OpenBB's standardized router.

    For B3 equities, the selected OpenBB provider is Yahoo Finance because the
    current official OpenBB provider catalog does not expose a dedicated B3
    connector. The provider-specific symbol convention is normalized here.
    """

    provider = "yfinance"

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        raw = symbol.strip().upper()
        if not raw:
            raise ValueError("Symbol is required")
        return raw if raw.endswith(".SA") else f"{raw}.SA"

    def historical(
        self,
        symbol: str,
        *,
        start: str | None = None,
        end: str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        normalized = self.normalize_symbol(symbol)
        try:
            from openbb import obb
        except ImportError as exc:
            raise RuntimeError("OpenBB is not installed") from exc

        kwargs: dict[str, object] = {
            "provider": self.provider,
            "interval": interval,
        }
        if start:
            kwargs["start_date"] = start
        if end:
            kwargs["end_date"] = end

        result = obb.equity.price.historical(normalized, **kwargs)
        df = result.to_df() if hasattr(result, "to_df") else pd.DataFrame(result)
        if df.empty:
            raise ValueError(f"No historical data returned for {symbol}")

        df = df.copy()
        if "date" in df.columns:
            df = df.set_index("date")
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        df.index.name = "date"
        df.columns = [str(c).lower() for c in df.columns]
        required = ["open", "high", "low", "close", "volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing market columns: {missing}")
        return df.sort_index()

    @staticmethod
    def quality(symbol: str, df: pd.DataFrame) -> MarketDataQuality:
        required = ("open", "high", "low", "close", "volume")
        missing = tuple(c for c in required if c not in df.columns)
        duplicates = int(df.index.duplicated().sum())
        nulls = int(df.loc[:, [c for c in required if c in df.columns]].isna().sum().sum())
        return MarketDataQuality(
            symbol=symbol,
            rows=len(df),
            required_columns=required,
            missing_columns=missing,
            duplicate_timestamps=duplicates,
            null_required_values=nulls,
            monotonic_timestamps=bool(df.index.is_monotonic_increasing),
        )

    def historical_with_quality(self, symbol: str, **kwargs: object) -> tuple[pd.DataFrame, MarketDataQuality]:
        df = self.historical(symbol, **kwargs)
        quality = self.quality(symbol, df)
        if not quality.valid:
            raise ValueError(f"Market data quality gate failed: {quality}")
        return df, quality


__all__ = ["B3_SYMBOLS", "MarketDataQuality", "OpenBBMarketDataProvider"]
