from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd


REQUIRED_OHLCV = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class MarketDataQualityReport:
    symbol: str
    rows: int
    start: str | None
    end: str | None
    required_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    duplicate_timestamps: int
    null_required_values: int
    nonfinite_required_values: int
    non_monotonic_timestamps: int
    invalid_ohlc_rows: int
    negative_volume_rows: int
    large_calendar_gaps: int
    max_gap_days: float

    @property
    def valid(self) -> bool:
        return (
            self.rows > 0
            and not self.missing_columns
            and self.duplicate_timestamps == 0
            and self.null_required_values == 0
            and self.nonfinite_required_values == 0
            and self.non_monotonic_timestamps == 0
            and self.invalid_ohlc_rows == 0
            and self.negative_volume_rows == 0
        )


def validate_market_data(symbol: str, df: pd.DataFrame, *, interval: str = "1d") -> MarketDataQualityReport:
    """Validate normalized OHLCV data without assuming weekends are trading days.

    Large gaps are reported for observability but do not by themselves fail the gate,
    because exchange holidays and corporate events can create legitimate gaps.
    """
    missing = tuple(c for c in REQUIRED_OHLCV if c not in df.columns)
    index = pd.DatetimeIndex(df.index) if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index, utc=True)
    rows = len(df)
    duplicate_count = int(index.duplicated().sum())
    non_monotonic = int((index[1:] < index[:-1]).sum()) if len(index) > 1 else 0

    start = index.min().isoformat() if len(index) else None
    end = index.max().isoformat() if len(index) else None

    if missing:
        return MarketDataQualityReport(
            symbol=symbol, rows=rows, start=start, end=end,
            required_columns=REQUIRED_OHLCV, missing_columns=missing,
            duplicate_timestamps=duplicate_count, null_required_values=0,
            nonfinite_required_values=0, non_monotonic_timestamps=non_monotonic,
            invalid_ohlc_rows=0, negative_volume_rows=0,
            large_calendar_gaps=0, max_gap_days=0.0,
        )

    values = df.loc[:, REQUIRED_OHLCV].apply(pd.to_numeric, errors="coerce")
    nulls = int(values.isna().sum().sum())
    finite = values.applymap(lambda x: math.isfinite(float(x)) if pd.notna(x) else False)
    nonfinite = int((~finite & values.notna()).sum().sum())

    invalid_ohlc = (
        (values["high"] < values[["open", "close", "low"]].max(axis=1))
        | (values["low"] > values[["open", "close", "high"]].min(axis=1))
        | (values[["open", "high", "low", "close"]] <= 0).any(axis=1)
    )
    invalid_ohlc_rows = int(invalid_ohlc.fillna(False).sum())
    negative_volume_rows = int((values["volume"] < 0).fillna(False).sum())

    gaps = index.sort_values().to_series().diff().dt.total_seconds().div(86400).dropna()
    max_gap = float(gaps.max()) if not gaps.empty else 0.0
    # More than four calendar days is suspicious for daily equity data, but not fatal.
    large_gaps = int((gaps > 4).sum()) if interval == "1d" else 0

    return MarketDataQualityReport(
        symbol=symbol, rows=rows, start=start, end=end,
        required_columns=REQUIRED_OHLCV, missing_columns=missing,
        duplicate_timestamps=duplicate_count, null_required_values=nulls,
        nonfinite_required_values=nonfinite, non_monotonic_timestamps=non_monotonic,
        invalid_ohlc_rows=invalid_ohlc_rows, negative_volume_rows=negative_volume_rows,
        large_calendar_gaps=large_gaps, max_gap_days=max_gap,
    )
