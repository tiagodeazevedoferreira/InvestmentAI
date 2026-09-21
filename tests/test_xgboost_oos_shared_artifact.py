from __future__ import annotations

import json

import pandas as pd
import pytest

from app.services.xgboost_oos import XGBoostOOSFold, XGBoostOOSRun
from app.services.xgboost_oos_artifact import (
    deserialize_xgboost_oos_run,
    load_xgboost_oos_artifact,
    serialize_xgboost_oos_run,
    write_xgboost_oos_artifact,
)


def _fixture() -> XGBoostOOSRun:
    index = pd.date_range("2025-01-01", periods=4, tz="UTC")
    probabilities = pd.Series([0.6, 0.4, 0.7, 0.3], index=index, name="probability")
    predictions = pd.Series([1, 0, 1, 0], index=index, name="prediction")
    folds = (
        XGBoostOOSFold(1, index[0], index[0], index[0], index[1]),
        XGBoostOOSFold(2, index[1], index[1], index[2], index[3]),
    )
    return XGBoostOOSRun(
        predictions=predictions,
        probabilities=probabilities,
        test_rows=4,
        folds=2,
        fold_metadata=folds,
    )


def test_oos_artifact_round_trip_preserves_predictions_and_fold_metadata(tmp_path) -> None:
    oos = _fixture()
    payload = serialize_xgboost_oos_run(
        oos,
        symbol="PETR4",
        configuration={"horizon": 5, "train_size": 500, "test_size": 100, "step": 100},
    )
    restored = deserialize_xgboost_oos_run(payload)

    assert restored.predictions.equals(oos.predictions)
    assert restored.probabilities.equals(oos.probabilities)
    assert restored.fold_metadata == oos.fold_metadata
    assert restored.test_rows == oos.test_rows
    assert restored.folds == oos.folds

    path = write_xgboost_oos_artifact(
        tmp_path / "PETR4.json",
        oos,
        symbol="PETR4",
        configuration=payload["configuration"],
    )
    loaded, loaded_payload = load_xgboost_oos_artifact(path)
    assert loaded.predictions.equals(oos.predictions)
    assert loaded_payload["symbol"] == "PETR4"


def test_oos_artifact_rejects_prediction_timestamps_outside_fold_ranges() -> None:
    payload = serialize_xgboost_oos_run(
        _fixture(),
        symbol="PETR4",
        configuration={},
    )
    payload["fold_metadata"][0]["test_end"] = "2026-01-01T00:00:00+00:00"

    with pytest.raises(ValueError, match="outside prediction timestamps"):
        deserialize_xgboost_oos_run(payload)


def test_oos_artifact_rejects_duplicate_timestamps() -> None:
    payload = serialize_xgboost_oos_run(
        _fixture(),
        symbol="PETR4",
        configuration={},
    )
    payload["predictions"][1]["timestamp"] = payload["predictions"][0]["timestamp"]

    with pytest.raises(ValueError, match="unique and chronological"):
        deserialize_xgboost_oos_run(payload)
