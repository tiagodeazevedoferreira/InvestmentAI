from __future__ import annotations

import pandas as pd
import pytest

from app.services.backtesting import BacktestConfig, Backtester
from app.services.market_replay import MarketReplay


def _bars() -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0, 130.0],
            "high": [101.0, 111.0, 121.0, 131.0],
            "low": [99.0, 109.0, 119.0, 129.0],
            "close": [100.0, 110.0, 120.0, 130.0],
            "volume": [1000.0, 1100.0, 1200.0, 1300.0],
        },
        index=index,
    )


def test_backtester_executes_signal_on_next_bar_open_and_liquidates_final_position() -> None:
    replay = MarketReplay("PETR4.SA", _bars())
    seen = []

    def signal(bar):
        seen.append((bar.timestamp, bar.close))
        if bar.close == 100.0:
            return 1
        if bar.close == 110.0:
            return -1
        return 0

    result = Backtester(BacktestConfig(initial_cash=1_000.0)).run(replay, signal)

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.final_cash == pytest.approx(1_090.9090909090908)
    assert list(result.equity.index) == list(_bars().index)
    assert seen[0][1] == 100.0
    assert result.equity.iloc[1] == pytest.approx(1_000.0)
    assert result.equity.iloc[2] == pytest.approx(1_090.9090909090908)


def test_backtester_applies_commission_and_slippage_deterministically() -> None:
    replay = MarketReplay("PETR4.SA", _bars())

    def signal(bar):
        if bar.close == 100.0:
            return 1
        if bar.close == 110.0:
            return -1
        return 0

    config = BacktestConfig(
        initial_cash=1_000.0,
        commission_rate=0.01,
        slippage_bps=100.0,
    )
    result = Backtester(config).run(replay, signal)

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.total_commission > 0.0
    assert result.total_slippage > 0.0
    assert result.final_cash < 1_090.9090909090908
    assert result.equity.iloc[-1] == pytest.approx(result.final_cash)


def test_backtester_rejects_invalid_signal() -> None:
    replay = MarketReplay("PETR4.SA", _bars())

    with pytest.raises(ValueError, match="signal_fn must return -1, 0, or 1"):
        Backtester().run(replay, lambda _bar: 2)
