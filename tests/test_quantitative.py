import numpy as np
import pandas as pd

from backend.app.services.evaluation import trading_metrics
from backend.app.services.features import build_features, chronological_split
from backend.app.services.portfolio import optimize_max_sharpe, parametric_var
from backend.app.services.simulator import MarketSimulator


def sample_ohlcv(n=120):
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series(100 + np.linspace(0, 20, n) + np.sin(np.arange(n)), index=idx)
    return pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1000}, index=idx)


def test_features_have_no_future_rows_and_split_is_chronological():
    X, y = build_features(sample_ohlcv(), 5)
    assert len(X) == len(y)
    assert len(X) > 50
    splits = chronological_split(X, y)
    assert splits[0][0].index.max() < splits[1][0].index.min() < splits[2][0].index.min()


def test_portfolio_optimizer_and_var():
    df = pd.DataFrame({"A": np.linspace(.001, .003, 100), "B": np.linspace(.002, .001, 100)})
    w, ret, vol, sharpe = optimize_max_sharpe(df)
    assert np.isclose(w.sum(), 1)
    assert 0 <= w.min() and w.max() <= 1
    assert np.isfinite([ret, vol, sharpe]).all()
    value = parametric_var(df, w, 10000, .95)
    assert value >= 0


def test_simulator_applies_trade_costs():
    sim = MarketSimulator(10000, commission_bps=10, slippage_bps=10)
    result = sim.step({"A": 100}, {"A": 1.0})
    assert result["positions"]["A"] > 0
    assert result["equity"] <= 10000


def test_financial_metrics():
    equity = pd.Series([100, 101, 99, 103, 105])
    metrics = trading_metrics(equity)
    assert np.isclose(metrics["total_return"], 0.05)
    assert metrics["max_drawdown"] < 0
