from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .model_engine import FEATURE_VERSION, predict_xgboost


class XGBoostInferenceError(RuntimeError):
    """Raised when a persisted XGBoost model cannot be safely used."""


def predict_with_artifact(X: pd.DataFrame, model_path: str) -> tuple[float, dict]:
    path = Path(model_path)
    metadata_path = path.with_suffix(".meta.json")

    if not path.is_file():
        raise XGBoostInferenceError(f"model artifact not found: {path}")
    if not metadata_path.is_file():
        raise XGBoostInferenceError(f"model metadata not found: {metadata_path}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise XGBoostInferenceError("invalid model metadata") from exc

    if metadata.get("feature_version") != FEATURE_VERSION:
        raise XGBoostInferenceError("model feature version is incompatible")

    expected = metadata.get("features")
    if not isinstance(expected, list) or not expected or not all(isinstance(v, str) for v in expected):
        raise XGBoostInferenceError("model metadata has no valid feature schema")

    actual = list(X.columns)
    if actual != expected:
        raise XGBoostInferenceError(
            f"feature schema mismatch: expected {expected}, received {actual}"
        )

    if X.empty:
        raise XGBoostInferenceError("no feature rows available for prediction")

    try:
        probability = predict_xgboost(X, str(path))
    except (OSError, ValueError, RuntimeError) as exc:
        raise XGBoostInferenceError("failed to load or run the XGBoost model") from exc

    if not 0.0 <= probability <= 1.0:
        raise XGBoostInferenceError("model probability is outside [0, 1]")

    return probability, metadata
