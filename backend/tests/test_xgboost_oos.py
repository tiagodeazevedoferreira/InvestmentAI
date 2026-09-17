from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.xgboost_oos import purged_xgboost_oos_predictions


def make_training_data(rows: int = 180):
    index = pd.date_range("2025-01-01", periods=rows, freq="D")
    rng = np.random.default_rng(42)

    X = pd.DataFrame(
        {
            "feature_a": rng.normal(size=rows),
            "feature_b": rng.normal(size=rows),
            "feature_c": rng.normal(size=rows),
        },
        index=index,
    )

    y = pd.Series(
        (X["feature_a"] + X["feature_b"] * 0.5 > 0).astype(int),
        index=index,
        name="target",
    )

    return X, y


def test_purged_xgboost_oos_is_timestamped_and_deterministic():
    X, y = make_training_data()

    params = {
        "n_estimators": 10,
        "max_depth": 2,
        "learning_rate": 0.1,
    }

    first = purged_xgboost_oos_predictions(
        X, y,
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        params=params,
    )

    second = purged_xgboost_oos_predictions(
        X, y,
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        params=params,
    )

    assert first.folds == 4
    assert first.test_rows == 80

    assert first.predictions.index.equals(first.probabilities.index)
    assert first.predictions.index.is_unique
    assert first.predictions.index.is_monotonic_increasing

    assert np.isfinite(first.probabilities.to_numpy()).all()
    assert ((first.probabilities >= 0) & (first.probabilities <= 1)).all()

    pd.testing.assert_series_equal(first.predictions, second.predictions)
    pd.testing.assert_series_equal(first.probabilities, second.probabilities)


def test_first_oos_window_respects_horizon_purge():
    X, y = make_training_data()

    result = purged_xgboost_oos_predictions(
        X, y,
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        params={
            "n_estimators": 5,
            "max_depth": 2,
            "learning_rate": 0.1,
        },
    )

    assert result.probabilities.index[0] == X.index[85]


def test_oos_windows_do_not_overlap():
    X, y = make_training_data()

    result = purged_xgboost_oos_predictions(
        X, y,
        horizon=5,
        train_size=80,
        test_size=20,
        step=20,
        params={
            "n_estimators": 5,
            "max_depth": 2,
            "learning_rate": 0.1,
        },
    )

    assert not result.probabilities.index.has_duplicates

    for previous, current in zip(
        result.probabilities.index[:-1],
        result.probabilities.index[1:],
    ):
        assert current > previous


def test_rejects_misaligned_indexes():
    X, y = make_training_data()
    y = y.copy()
    y.index = pd.date_range("2026-01-01", periods=len(y), freq="D")

    with pytest.raises(ValueError, match="identical indexes"):
        purged_xgboost_oos_predictions(
            X, y,
            horizon=5,
            train_size=80,
            test_size=20,
            step=20,
            params={"n_estimators": 5},
        )


def test_rejects_non_chronological_features():
    X, y = make_training_data()
    X = X.iloc[::-1]
    y = y.loc[X.index]

    with pytest.raises(ValueError, match="chronological"):
        purged_xgboost_oos_predictions(
            X, y,
            horizon=5,
            train_size=80,
            test_size=20,
            step=20,
            params={"n_estimators": 5},
        )


def test_rejects_insufficient_observations():
    X, y = make_training_data(rows=100)

    with pytest.raises(ValueError, match="insufficient observations"):
        purged_xgboost_oos_predictions(
            X, y,
            horizon=5,
            train_size=80,
            test_size=20,
            step=20,
            params={"n_estimators": 5},
        )
