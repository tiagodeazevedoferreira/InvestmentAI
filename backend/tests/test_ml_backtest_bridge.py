from __future__ import annotations

import pandas as pd
import pytest

from app.services.market_replay import MarketBar
from app.services.ml_trading import (
    probabilities_to_signals,
    signals_to_backtest_function,
)


def _probabilities() -> pd.Series:
    index = pd.date_range("2026-01-01", periods=5, freq="D", tz="UTC")
    return pd.Series(
        [0.40, 0.60, 0.75, 0.50, 0.25],
        index=index,
        name="probability",
    )


def _bar(timestamp: str) -> MarketBar:
    return MarketBar(
        symbol="PETR4.SA",
        timestamp=pd.Timestamp(timestamp),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000.0,
    )


def test_probabilities_to_signals_preserves_timestamps_and_threshold() -> None:
    probabilities = _probabilities()

    signals = probabilities_to_signals(probabilities, threshold=0.60)

    assert list(signals.index) == list(probabilities.index)
    assert signals.name == "signal"
    assert signals.tolist() == [-1, 1, 1, -1, -1]


def test_probabilities_to_signals_accepts_explicit_threshold() -> None:
    probabilities = _probabilities()

    signals = probabilities_to_signals(probabilities, threshold=0.40)

    assert signals.tolist() == [1, 1, 1, 1, -1]


def test_probabilities_to_signals_rejects_invalid_probability() -> None:
    probabilities = _probabilities()
    probabilities.iloc[2] = 1.1

    with pytest.raises(ValueError, match="probabilities must be finite values in \\[0, 1\\]"):
        probabilities_to_signals(probabilities)


def test_probabilities_to_signals_rejects_duplicate_timestamps() -> None:
    probabilities = _probabilities()
    probabilities.index = [
        probabilities.index[0],
        probabilities.index[1],
        probabilities.index[1],
        probabilities.index[3],
        probabilities.index[4],
    ]

    with pytest.raises(ValueError, match="probabilities index must be unique"):
        probabilities_to_signals(probabilities)


def test_probabilities_to_signals_rejects_non_chronological_timestamps() -> None:
    probabilities = _probabilities().iloc[[0, 2, 1, 3, 4]]

    with pytest.raises(ValueError, match="probabilities index must be chronological"):
        probabilities_to_signals(probabilities)


def test_probabilities_to_signals_rejects_invalid_threshold() -> None:
    probabilities = _probabilities()

    with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
        probabilities_to_signals(probabilities, threshold=1.5)


def test_signals_to_backtest_function_returns_signal_for_matching_timestamp() -> None:
    probabilities = _probabilities()
    signals = probabilities_to_signals(probabilities, threshold=0.60)

    signal_fn = signals_to_backtest_function(signals)

    assert signal_fn(_bar("2026-01-01T00:00:00Z")) == -1
    assert signal_fn(_bar("2026-01-02T00:00:00Z")) == 1
    assert signal_fn(_bar("2026-01-03T00:00:00Z")) == 1


def test_signals_to_backtest_function_returns_hold_for_missing_timestamp() -> None:
    probabilities = _probabilities()
    signals = probabilities_to_signals(probabilities, threshold=0.60)

    signal_fn = signals_to_backtest_function(signals)

    assert signal_fn(_bar("2026-01-10T00:00:00Z")) == 0


def test_signals_to_backtest_function_rejects_duplicate_signal_timestamps() -> None:
    signals = pd.Series(
        [1, -1],
        index=pd.DatetimeIndex(
            [
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ]
        ),
        name="signal",
    )

    with pytest.raises(ValueError, match="signals index must be unique"):
        signals_to_backtest_function(signals)


def test_signals_to_backtest_function_rejects_invalid_signal_values() -> None:
    signals = pd.Series(
        [1, 2],
        index=pd.date_range("2026-01-01", periods=2, freq="D", tz="UTC"),
        name="signal",
    )

    with pytest.raises(ValueError, match="signals must contain only -1, 0, or 1"):
        signals_to_backtest_function(signals)


def test_ml_signals_integrate_with_backtester_using_next_bar_open() -> None:
    from app.services.backtesting import BacktestConfig, Backtester
    from app.services.market_replay import MarketReplay

    index = pd.date_range("2026-01-01", periods=4, freq="D", tz="UTC")
    bars = pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0, 130.0],
            "high": [101.0, 111.0, 121.0, 131.0],
            "low": [99.0, 109.0, 119.0, 129.0],
            "close": [100.0, 105.0, 120.0, 130.0],
            "volume": [1000.0, 1000.0, 1000.0, 1000.0],
        },
        index=index,
    )

    signals = pd.Series(
        [1, -1],
        index=index[:2],
        name="signal",
    )

    result = Backtester(
        BacktestConfig(initial_cash=1_000.0)
    ).run(
        MarketReplay("PETR4.SA", bars),
        signals_to_backtest_function(signals),
    )

    expected_final_cash = 1_000.0 * 120.0 / 110.0

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.final_cash == pytest.approx(expected_final_cash)

    assert result.equity.iloc[0] == pytest.approx(1_000.0)

    expected_t1_equity = (1_000.0 / 110.0) * 105.0
    assert result.equity.iloc[1] == pytest.approx(expected_t1_equity)

    assert result.equity.iloc[2] == pytest.approx(expected_final_cash)


def test_ml_signals_integration_applies_backtest_costs() -> None:
    from app.services.backtesting import BacktestConfig, Backtester
    from app.services.market_replay import MarketReplay

    index = pd.date_range("2026-01-01", periods=4, freq="D", tz="UTC")
    bars = pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0, 130.0],
            "high": [101.0, 111.0, 121.0, 131.0],
            "low": [99.0, 109.0, 119.0, 129.0],
            "close": [100.0, 105.0, 120.0, 130.0],
            "volume": [1000.0, 1000.0, 1000.0, 1000.0],
        },
        index=index,
    )

    signals = pd.Series(
        [1, -1],
        index=index[:2],
        name="signal",
    )

    result = Backtester(
        BacktestConfig(
            initial_cash=1_000.0,
            commission_rate=0.01,
            slippage_bps=100.0,
        )
    ).run(
        MarketReplay("PETR4.SA", bars),
        signals_to_backtest_function(signals),
    )

    expected_no_cost_final_cash = 1_000.0 * 120.0 / 110.0

    assert result.trades == 2
    assert result.final_position == 0.0
    assert result.total_commission > 0.0
    assert result.total_slippage > 0.0
    assert result.final_cash < expected_no_cost_final_cash
