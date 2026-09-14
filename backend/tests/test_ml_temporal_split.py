from __future__ import annotations

import pandas as pd
import pytest

from app.services.features import chronological_split


def _dataset(size: int = 100) -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2026-01-01", periods=size, freq="D", tz="UTC")
    X = pd.DataFrame({"feature": range(size)}, index=index)
    y = pd.Series(range(size), index=index, name="target")
    return X, y


def test_chronological_split_preserves_current_behavior_without_purge() -> None:
    X, y = _dataset()

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = chronological_split(
        X,
        y,
        train_fraction=0.7,
        validation_fraction=0.15,
    )

    assert len(X_train) == 70
    assert len(X_val) == 15
    assert len(X_test) == 15

    assert X_train.index[-1] < X_val.index[0]
    assert X_val.index[-1] < X_test.index[0]

    assert y_train.iloc[-1] == 69
    assert y_val.iloc[0] == 70
    assert y_val.iloc[-1] == 84
    assert y_test.iloc[0] == 85


def test_chronological_split_purges_horizon_from_train_and_validation() -> None:
    X, y = _dataset()

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = chronological_split(
        X,
        y,
        train_fraction=0.7,
        validation_fraction=0.15,
        purge_bars=5,
    )

    assert len(X_train) == 65
    assert len(X_val) == 10
    assert len(X_test) == 15

    assert y_train.iloc[-1] == 64
    assert y_val.iloc[0] == 70
    assert y_val.iloc[-1] == 79
    assert y_test.iloc[0] == 85

    assert set(X_train.index).isdisjoint(X_val.index)
    assert set(X_val.index).isdisjoint(X_test.index)

    assert X_train.index[-1] < X_val.index[0]
    assert X_val.index[-1] < X_test.index[0]


def test_chronological_split_rejects_negative_purge() -> None:
    X, y = _dataset()

    with pytest.raises(ValueError, match="purge_bars must be non-negative"):
        chronological_split(X, y, purge_bars=-1)
