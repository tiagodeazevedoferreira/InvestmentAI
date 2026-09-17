from __future__ import annotations

import pandas as pd

from app.services.backtesting import BacktestConfig, Backtester
from app.services.market_replay import MarketReplay


def make_bars() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=4, freq="D")

    return pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0, 130.0],
            "high": [105.0, 115.0, 125.0, 135.0],
            "low": [95.0, 105.0, 115.0, 125.0],
            "close": [100.0, 110.0, 120.0, 130.0],
            "volume": [1000.0, 1000.0, 1000.0, 1000.0],
        },
        index=index,
    )


def test_signal_on_bar_t_executes_on_next_bar_open():
    replay = MarketReplay("TEST", make_bars())

    signals = {
        pd.Timestamp("2025-01-01"): 1,
        pd.Timestamp("2025-01-02"): -1,
        pd.Timestamp("2025-01-03"): 0,
        pd.Timestamp("2025-01-04"): 0,
    }

    result = Backtester(
        BacktestConfig(initial_cash=10_000.0)
    ).run(
        replay,
        lambda bar: signals.get(bar.timestamp, 0),
    )

    expected_final_cash = (10_000.0 / 110.0) * 120.0

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.final_cash == expected_final_cash


def test_signal_does_not_execute_on_same_bar_close():
    replay = MarketReplay("TEST", make_bars())

    result = Backtester(
        BacktestConfig(initial_cash=10_000.0)
    ).run(
        replay,
        lambda bar: 1 if bar.timestamp == pd.Timestamp("2025-01-01") else 0,
    )

    expected_position = 10_000.0 / 110.0

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.final_cash == expected_position * 130.0


def test_no_oos_signal_can_execute_before_first_oos_timestamp():
    replay = MarketReplay("TEST", make_bars())

    first_oos = pd.Timestamp("2025-01-03")

    signals = {
        first_oos: 1,
    }

    result = Backtester(
        BacktestConfig(initial_cash=10_000.0)
    ).run(
        replay,
        lambda bar: signals.get(bar.timestamp, 0),
    )

    assert result.trades == 2
    assert result.final_position == 0.0
