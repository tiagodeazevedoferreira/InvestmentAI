from __future__ import annotations

import pandas as pd

from .data_quality import MarketDataQualityReport, REQUIRED_OHLCV, validate_market_data


B3_SYMBOLS = {"PETR4", "VALE3", "ITUB4"}


class OpenBBMarketDataProvider:
    """Market-data adapter using OpenBB's standardized router.

    Provider-specific conventions are normalized at the adapter boundary so the
    rest of the application receives the canonical internal OHLCV contract.
    """

    provider = "yfinance"

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        raw = symbol.strip().upper()
        if not raw:
            raise ValueError("Symbol is required")
        return raw if raw.endswith(".SA") else f"{raw}.SA"

    @staticmethod
    def normalize_historical_frame(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize an adapter result to the canonical internal OHLCV schema."""
        if df is None or df.empty:
            raise ValueError("No historical market data available")

        out = df.copy()
        if "date" in out.columns:
            out = out.set_index("date")
        if not isinstance(out.index, pd.DatetimeIndex):
            out.index = pd.to_datetime(out.index, utc=True)
        out.index.name = "date"

        column_map = {str(column).strip().lower(): column for column in out.columns}
        missing = [column for column in ("open", "high", "low", "close", "volume") if column not in column_map]
        if missing:
            raise ValueError(f"Missing market columns: {missing}")

        normalized = out.rename(columns={column_map[key]: key.title() for key in column_map})
        duplicate_columns = normalized.columns[normalized.columns.duplicated()].tolist()
        if duplicate_columns:
            raise ValueError(f"Duplicate normalized market columns: {duplicate_columns}")

        return normalized.sort_index()

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
        return self.normalize_historical_frame(df)

    @staticmethod
    def quality(symbol: str, df: pd.DataFrame, *, interval: str = "1d") -> MarketDataQualityReport:
        return validate_market_data(symbol, df, interval=interval)

    def historical_with_quality(
        self, symbol: str, **kwargs: object
    ) -> tuple[pd.DataFrame, MarketDataQualityReport]:
        interval = str(kwargs.get("interval", "1d"))
        df = self.historical(symbol, **kwargs)
        quality = validate_market_data(symbol, df, interval=interval)
        if not quality.valid:
            raise ValueError(f"Market data quality gate failed: {quality}")
        return df, quality


__all__ = [
    "B3_SYMBOLS",
    "MarketDataQualityReport",
    "OpenBBMarketDataProvider",
    "REQUIRED_OHLCV",
]
