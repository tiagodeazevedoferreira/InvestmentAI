from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .xgboost_oos import XGBoostOOSFold, XGBoostOOSRun

SCHEMA_VERSION = 1


def _timestamp(value: pd.Timestamp) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat()


def _parse_timestamp(value: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def serialize_xgboost_oos_run(
    oos: XGBoostOOSRun, *, symbol: str, configuration: dict, source: dict | None = None,
 ) -> dict:
    if not isinstance(oos, XGBoostOOSRun):
        raise ValueError("oos must be an XGBoostOOSRun")
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol cannot be empty")
    if not oos.probabilities.index.equals(oos.predictions.index):
        raise ValueError("OOS predictions and probabilities must have identical indexes")
    if not oos.probabilities.index.is_unique or not oos.probabilities.index.is_monotonic_increasing:
        raise ValueError("OOS prediction index must be unique and chronological")
    probabilities = oos.probabilities.astype(float)
    predictions = oos.predictions.astype(int)
    values = probabilities.to_numpy(dtype=float)
    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("OOS probabilities must be finite and within [0, 1]")
    if not predictions.isin([0, 1]).all():
        raise ValueError("OOS predictions must be binary")
    if len(probabilities) != oos.test_rows or len(oos.fold_metadata) != oos.folds:
        raise ValueError("OOS size metadata is inconsistent")
    rows = [{"timestamp": _timestamp(index), "prediction": int(predictions.loc[index]), "probability": float(probabilities.loc[index])} for index in probabilities.index]
    folds = [{"fold": int(fold.fold), "train_start": _timestamp(fold.train_start), "train_end": _timestamp(fold.train_end), "test_start": _timestamp(fold.test_start), "test_end": _timestamp(fold.test_end)} for fold in oos.fold_metadata]
    return {"schema_version": SCHEMA_VERSION, "symbol": normalized_symbol, "configuration": configuration, "source": source or {}, "test_rows": int(oos.test_rows), "folds": int(oos.folds), "predictions": rows, "fold_metadata": folds}


def deserialize_xgboost_oos_run(payload: dict) -> XGBoostOOSRun:
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported OOS artifact schema_version")
    rows = payload.get("predictions")
    fold_rows = payload.get("fold_metadata")
    if not isinstance(rows, list) or not rows:
        raise ValueError("OOS artifact predictions must be a non-empty list")
    if not isinstance(fold_rows, list) or not fold_rows:
        raise ValueError("OOS artifact fold_metadata must be a non-empty list")
    index = pd.DatetimeIndex([_parse_timestamp(row["timestamp"]) for row in rows])
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError("OOS artifact prediction timestamps must be unique and chronological")
    predictions = pd.Series([int(row["prediction"]) for row in rows], index=index, name="prediction", dtype=int)
    probabilities = pd.Series([float(row["probability"]) for row in rows], index=index, name="probability", dtype=float)
    if not predictions.isin([0, 1]).all():
        raise ValueError("OOS artifact predictions must be binary")
    values = probabilities.to_numpy(dtype=float)
    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("OOS artifact probabilities must be finite and within [0, 1]")
    folds = []
    for row in fold_rows:
        fold = XGBoostOOSFold(fold=int(row["fold"]), train_start=_parse_timestamp(row["train_start"]), train_end=_parse_timestamp(row["train_end"]), test_start=_parse_timestamp(row["test_start"]), test_end=_parse_timestamp(row["test_end"]))
        if fold.test_start > fold.test_end or fold.train_start > fold.train_end:
            raise ValueError("OOS artifact fold ranges are invalid")
        folds.append(fold)
    if [fold.fold for fold in folds] != list(range(1, len(folds) + 1)):
        raise ValueError("OOS artifact fold numbering must be contiguous from 1")
    for previous, current in zip(folds, folds[1:]):
        if previous.test_end >= current.test_start:
            raise ValueError("OOS artifact fold test windows overlap")
    if len(predictions) != int(payload.get("test_rows", -1)) or len(folds) != int(payload.get("folds", -1)):
        raise ValueError("OOS artifact size metadata is inconsistent")
    return XGBoostOOSRun(predictions=predictions, probabilities=probabilities, test_rows=len(predictions), folds=len(folds), fold_metadata=tuple(folds))


def write_xgboost_oos_artifact(path: str | Path, oos: XGBoostOOSRun, *, symbol: str, configuration: dict, source: dict | None = None) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_xgboost_oos_run(oos, symbol=symbol, configuration=configuration, source=source)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def load_xgboost_oos_artifact(path: str | Path) -> tuple[XGBoostOOSRun, dict]:
    artifact_path = Path(path)
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"unable to read OOS artifact: {artifact_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid OOS artifact JSON: {artifact_path}") from exc
    return deserialize_xgboost_oos_run(payload), payload
