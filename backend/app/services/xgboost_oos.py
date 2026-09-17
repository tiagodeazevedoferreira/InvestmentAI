from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtesting import BacktestConfig, BacktestResult, Backtester
from .features import build_features
from .market_replay import MarketReplay
from .ml_trading import probabilities_to_signals, signals_to_backtest_function


@dataclass(frozen=True)
class XGBoostOOSRun:
    predictions: pd.Series
    probabilities: pd.Series
    test_rows: int
    folds: int


def _default_params() -> dict:
    return {
        "n_estimators": 300,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "eval_metric": "logloss",
    }


def purged_xgboost_oos_predictions(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    horizon: int = 5,
    train_size: int = 500,
    test_size: int = 100,
    step: int = 100,
    params: dict | None = None,
) -> XGBoostOOSRun:
    """Generate deterministic, timestamped purged walk-forward XGBoost predictions.

    The test window starts ``horizon`` observations after the end of the
    training window, preventing the target horizon from leaking across the
    train/test boundary.
    """
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("xgboost is not installed") from exc

    if not isinstance(X, pd.DataFrame):
        raise ValueError("X must be a pandas DataFrame")
    if not isinstance(y, pd.Series):
        raise ValueError("y must be a pandas Series")
    if len(X) != len(y):
        raise ValueError("X and y must have the same number of rows")
    if len(X) == 0:
        raise ValueError("X and y cannot be empty")

    for name, value in (
        ("horizon", horizon),
        ("train_size", train_size),
        ("test_size", test_size),
        ("step", step),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    if not X.index.equals(y.index):
        raise ValueError("X and y must have identical indexes")
    if not X.index.is_unique:
        raise ValueError("X index must be unique")
    if not X.index.is_monotonic_increasing:
        raise ValueError("X index must be chronological")

    minimum_rows = train_size + horizon + test_size
    if len(X) < minimum_rows:
        raise ValueError("insufficient observations for purged walk-forward predictions")

    if y.isna().any():
        raise ValueError("y cannot contain missing values")

    model_params = _default_params()
    model_params.update(params or {})

    predictions: list[pd.Series] = []
    probabilities: list[pd.Series] = []

    start = 0
    folds = 0

    while start + train_size + horizon + test_size <= len(X):
        train_end = start + train_size
        test_start = train_end + horizon
        test_end = test_start + test_size

        X_train = X.iloc[start:train_end]
        y_train = y.iloc[start:train_end]
        X_test = X.iloc[test_start:test_end]

        if y_train.nunique() < 2:
            start += step
            continue

        model = XGBClassifier(**model_params)
        model.fit(X_train, y_train, verbose=False)

        probability = model.predict_proba(X_test)[:, 1]
        prediction = model.predict(X_test)

        predictions.append(
            pd.Series(
                prediction.astype(int),
                index=X_test.index,
                name="prediction",
            )
        )
        probabilities.append(
            pd.Series(
                probability.astype(float),
                index=X_test.index,
                name="probability",
            )
        )

        folds += 1
        start += step

    if not predictions:
        raise ValueError("no valid XGBoost walk-forward prediction folds were produced")

    pred = pd.concat(predictions).sort_index()
    prob = pd.concat(probabilities).sort_index()

    if pred.index.has_duplicates:
        raise ValueError("XGBoost OOS prediction windows overlap")

    probability_values = prob.to_numpy(dtype=float)
    if not np.isfinite(probability_values).all():
        raise ValueError("XGBoost OOS probabilities contain non-finite values")

    if not ((probability_values >= 0.0) & (probability_values <= 1.0)).all():
        raise ValueError("XGBoost OOS probabilities must be within [0, 1]")

    return XGBoostOOSRun(
        predictions=pred,
        probabilities=prob,
        test_rows=len(prob),
        folds=folds,
    )


def run_xgboost_oos_backtest(
    history: pd.DataFrame,
    *,
    symbol: str,
    horizon: int = 5,
    train_size: int = 500,
    test_size: int = 100,
    step: int = 100,
    threshold: float = 0.60,
    backtest_config: BacktestConfig | None = None,
    params: dict | None = None,
) -> tuple[XGBoostOOSRun, BacktestResult]:
    """Run the offline XGBoost OOS → signal → deterministic backtest contract.

    The replay is restricted to the OOS prediction interval plus the first bar
    needed to execute the final OOS signal at the next bar open. This prevents
    pre-OOS and post-OOS market data from affecting economic backtest results.
    """
    if not isinstance(history, pd.DataFrame):
        raise ValueError("history must be a pandas DataFrame")

    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol cannot be empty")

    column_map = {str(column).lower(): column for column in history.columns}
    required = ("open", "high", "low", "close", "volume")
    missing = [column for column in required if column not in column_map]
    if missing:
        raise ValueError(f"history is missing required OHLCV columns: {missing}")

    normalized_history = history.rename(
        columns={column_map[name]: name.title() for name in required}
    ).copy()

    X, y = build_features(normalized_history, horizon=horizon)

    oos = purged_xgboost_oos_predictions(
        X,
        y,
        horizon=horizon,
        train_size=train_size,
        test_size=test_size,
        step=step,
        params=params,
    )

    signals = probabilities_to_signals(
        oos.probabilities,
        threshold=threshold,
    )

    signal_fn = signals_to_backtest_function(signals)

    replay_data = normalized_history.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    history_index = pd.DatetimeIndex(replay_data.index)
    if not history_index.is_unique:
        raise ValueError("history index must be unique")
    if not history_index.is_monotonic_increasing:
        raise ValueError("history index must be chronological")

    first_oos = pd.Timestamp(oos.probabilities.index.min())
    last_oos = pd.Timestamp(oos.probabilities.index.max())
    if first_oos not in history_index or last_oos not in history_index:
        raise ValueError("OOS prediction timestamps must be present in history")

    first_position = history_index.get_loc(first_oos)
    last_position = history_index.get_loc(last_oos)
    if not isinstance(first_position, (int, np.integer)) or not isinstance(last_position, (int, np.integer)):
        raise ValueError("history index lookup must resolve to unique positions")

    replay_end = last_position + 1
    if replay_end >= len(replay_data):
        raise ValueError("history must contain a bar after the final OOS prediction")

    replay_data = replay_data.iloc[first_position : replay_end + 1]

    replay = MarketReplay(
        symbol=normalized_symbol,
        data=replay_data,
    )

    result = Backtester(backtest_config).run(
        replay,
        signal_fn,
    )

    if result.final_position != 0.0:
        raise ValueError("backtest must finish with no open position")

    if not np.isfinite(result.final_cash):
        raise ValueError("backtest final cash must be finite")

    if result.total_commission < 0 or result.total_slippage < 0:
        raise ValueError("backtest costs cannot be negative")

    return oos, result
