from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pandas as pd


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketReplay:
    """Deterministically replay normalized OHLCV data in chronological order.

    The replay exposes only the current bar to the consumer. It never sorts after
    iteration starts and does not expose future rows through the public iterator.
    """

    def __init__(self, symbol: str, data: pd.DataFrame) -> None:
        required = ("open", "high", "low", "close", "volume")
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"missing required columns: {missing}")

        frame = data.loc[:, required].copy()
        index = pd.DatetimeIndex(frame.index)
        if not index.is_monotonic_increasing:
            raise ValueError("market replay requires chronological data")
        if index.has_duplicates:
            raise ValueError("market replay does not accept duplicate timestamps")
        if len(frame) == 0:
            raise ValueError("market replay requires at least one bar")

        self._symbol = symbol
        self._data = frame

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def total_bars(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[MarketBar]:
        for timestamp, row in self._data.iterrows():
            yield MarketBar(
                symbol=self._symbol,
                timestamp=pd.Timestamp(timestamp),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
