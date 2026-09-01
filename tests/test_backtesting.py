import pandas as pd
import pytest

from backend.app.services.backtesting import BacktestConfig, Backtester
from backend.app.services.market_replay import MarketReplay


def replay():
    index = pd.date_range("2026-01-01", periods=4, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0, 115.0],
            "high": [105.0, 115.0, 125.0, 120.0],
            "low": [95.0, 105.0, 115.0, 110.0],
            "close": [110.0, 120.0, 115.0, 118.0],
            "volume": [1000.0] * 4,
        },
        index=index,
    )
    return MarketReplay("TEST", frame)


def test_signal_executes_on_next_open_and_final_liquidation():
    result = Backtester(BacktestConfig(initial_cash=1000)).run(replay(), lambda bar: 1 if bar.timestamp.day == 1 else -1)
    assert result.trades == 2
    assert result.final_position == 0
    # Signal on day 1 buys at day 2 open (110), then day 2 signal exits at day 3 open (120).
    assert result.final_cash == pytest.approx(1000 * 120 / 110)


def test_commission_and_slippage_reduce_result():
    config = BacktestConfig(initial_cash=1000, commission_rate=0.001, slippage_bps=10)
    result = Backtester(config).run(replay(), lambda bar: 1 if bar.timestamp.day == 1 else -1)
    assert result.total_commission > 0
    assert result.total_slippage > 0
    assert result.final_cash < 1000 * 120 / 110


def test_invalid_signal_is_rejected():
    with pytest.raises(ValueError, match="signal_fn must return"):
        Backtester().run(replay(), lambda bar: 2)
