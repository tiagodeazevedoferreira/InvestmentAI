from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from app.services.backtesting import BacktestConfig
from app.services.features import build_features
from app.services.model_engine import predict_xgboost
from app.services.xgboost_baseline import train_symbol_baseline
from app.services.xgboost_oos import run_xgboost_oos_backtest


def _history(rows: int = 180) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="D", tz="UTC")
    close = 100.0 + np.linspace(0.0, 20.0, rows) + 2.0 * np.sin(np.arange(rows) / 5.0)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(rows, 1000.0),
        },
        index=index,
    )


def test_real_pipeline_contract_train_artifact_then_oos_backtest(tmp_path):
    history = _history()
    calls: list[tuple[str, str]] = []

    def provider(symbol: str, period: str) -> pd.DataFrame:
        calls.append((symbol, period))
        return history.copy()

    model_path = tmp_path / "model.json"
    metadata = train_symbol_baseline("TEST", "synthetic", str(model_path), provider, horizon=5)

    assert calls == [("TEST", "synthetic")]
    assert model_path.is_file()
    assert Path(metadata["metadata_path"]).is_file()

    X, _ = build_features(history, horizon=5)
    probability = predict_xgboost(X.iloc[[-1]], str(model_path))
    assert 0.0 <= probability <= 1.0

    oos, result = run_xgboost_oos_backtest(
        history,
        symbol="TEST",
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        threshold=0.60,
        backtest_config=BacktestConfig(
            initial_cash=100_000.0,
            commission_rate=0.001,
            slippage_bps=5.0,
        ),
        params={
            "n_estimators": 20,
            "max_depth": 2,
            "learning_rate": 0.1,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 42,
            "eval_metric": "logloss",
        },
    )

    assert oos.folds > 0
    assert oos.test_rows == len(oos.probabilities)
    assert oos.probabilities.index.is_unique
    assert oos.probabilities.index.is_monotonic_increasing
    assert result.final_position == 0.0
    assert np.isfinite(result.final_cash)
    assert result.total_commission >= 0.0
    assert result.total_slippage >= 0.0


def test_train_pipeline_fails_closed_on_non_dataframe_provider_output(tmp_path):
    def provider(symbol: str, period: str):
        return None

    try:
        train_symbol_baseline("TEST", "synthetic", str(tmp_path / "model.json"), provider, horizon=5)
    except ValueError as exc:
        assert str(exc) == "history_provider must return a pandas DataFrame"
    else:
        raise AssertionError("invalid provider output must fail closed")
