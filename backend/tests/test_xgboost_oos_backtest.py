from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.backtesting import BacktestConfig
from app.services.xgboost_oos import run_xgboost_oos_backtest


def make_ohlcv(rows: int = 260) -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=rows, freq="D")

    rng = np.random.default_rng(42)
    returns = rng.normal(0.001, 0.02, rows)

    close = 100.0 * np.cumprod(1.0 + returns)
    open_price = close * (1.0 + rng.normal(0.0, 0.003, rows))

    high = np.maximum(open_price, close) * (
        1.0 + rng.uniform(0.001, 0.01, rows)
    )
    low = np.minimum(open_price, close) * (
        1.0 - rng.uniform(0.001, 0.01, rows)
    )

    volume = rng.integers(100_000, 500_000, rows).astype(float)

    return pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_xgboost_oos_runs_end_to_end_into_backtester():
    history = make_ohlcv()

    oos, result = run_xgboost_oos_backtest(
        history,
        symbol="PETR4",
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        threshold=0.60,
        backtest_config=BacktestConfig(
            initial_cash=10_000.0,
            commission_rate=0.001,
            slippage_bps=5.0,
        ),
        params={
            "n_estimators": 10,
            "max_depth": 2,
            "learning_rate": 0.1,
        },
    )

    assert oos.folds > 0
    assert oos.test_rows > 0

    assert oos.predictions.index.equals(oos.probabilities.index)
    assert oos.probabilities.index.is_unique
    assert oos.probabilities.index.is_monotonic_increasing

    assert result.final_position == 0.0
    assert np.isfinite(result.final_cash)

    assert result.trades >= 0
    assert result.total_commission >= 0.0
    assert result.total_slippage >= 0.0

    assert len(result.equity) == len(history)
    assert result.equity.index.equals(history.index)


def test_xgboost_oos_backtest_accepts_lowercase_ohlcv_columns():
    history = make_ohlcv()
    history.columns = [column.lower() for column in history.columns]

    oos, result = run_xgboost_oos_backtest(
        history,
        symbol="VALE3",
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        threshold=0.60,
        backtest_config=BacktestConfig(initial_cash=10_000.0),
        params={
            "n_estimators": 5,
            "max_depth": 2,
            "learning_rate": 0.1,
        },
    )

    assert oos.test_rows > 0
    assert result.final_position == 0.0
    assert np.isfinite(result.final_cash)
