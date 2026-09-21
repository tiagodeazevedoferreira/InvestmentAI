import numpy as np
import pandas as pd

from app.services.backtesting import BacktestConfig
from app.services.xgboost_oos import run_xgboost_oos_backtest


def _synthetic_ohlcv(rows: int = 900) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=rows, freq="D")
    close = 100.0 + np.cumsum(
        0.25 * np.sin(np.arange(rows) / 17.0)
        + 0.08 * np.cos(np.arange(rows) / 7.0)
    )
    open_ = close + 0.15 * np.sin(np.arange(rows) / 5.0)
    high = np.maximum(open_, close) + 0.5
    low = np.minimum(open_, close) - 0.5
    volume = 1_000_000.0 + 10_000.0 * np.cos(np.arange(rows) / 13.0)

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_xgboost_oos_economic_backtest_respects_oos_replay_boundary():
    history = _synthetic_ohlcv()
    config = BacktestConfig(
        initial_cash=100_000.0,
        commission_rate=0.001,
        slippage_bps=5.0,
    )

    oos, result = run_xgboost_oos_backtest(
        history,
        symbol="TEST",
        horizon=5,
        train_size=500,
        test_size=100,
        step=100,
        threshold=0.60,
        backtest_config=config,
    )

    assert oos.folds > 0
    assert oos.test_rows == len(oos.probabilities)
    assert result.final_position == 0.0
    assert np.isfinite(result.final_cash)
    assert result.total_commission >= 0.0
    assert result.total_slippage >= 0.0

    expected_start = oos.probabilities.index.min()
    expected_last_oos = oos.probabilities.index.max()
    history_index = pd.DatetimeIndex(history.index)
    last_oos_position = history_index.get_loc(expected_last_oos)
    expected_replay_end = history_index[last_oos_position + 1]

    assert result.equity.index[0] == expected_start
    assert result.equity.index[-1] == expected_replay_end
