import numpy as np
import pandas as pd
import pytest

from backend.app.services.model_engine import train_xgboost
from backend.app.services.xgboost_inference import XGBoostInferenceError, predict_with_artifact


def _trained_model(tmp_path):
    rng = np.random.default_rng(123)
    n = 200
    X = pd.DataFrame({"feature_a": rng.normal(size=n), "feature_b": rng.normal(size=n)})
    y = pd.Series((X["feature_a"] + X["feature_b"] > 0).astype(int))
    path = tmp_path / "baseline.json"
    train_xgboost(X, y, str(path), params={"n_estimators": 20, "max_depth": 2})
    return path


def test_predict_with_artifact_validates_schema_and_returns_probability(tmp_path):
    path = _trained_model(tmp_path)
    X = pd.DataFrame({"feature_a": [0.1], "feature_b": [-0.2]})

    probability, metadata = predict_with_artifact(X, str(path))

    assert 0.0 <= probability <= 1.0
    assert metadata["feature_version"] == "technical-v1"
    assert metadata["features"] == ["feature_a", "feature_b"]


def test_predict_with_artifact_rejects_feature_schema_mismatch(tmp_path):
    path = _trained_model(tmp_path)
    X = pd.DataFrame({"feature_b": [0.1], "feature_a": [-0.2]})

    with pytest.raises(XGBoostInferenceError, match="feature schema mismatch"):
        predict_with_artifact(X, str(path))


def test_predict_with_artifact_requires_metadata(tmp_path):
    path = tmp_path / "missing.json"
    path.write_text("{}", encoding="utf-8")
    X = pd.DataFrame({"feature_a": [0.1]})

    with pytest.raises(XGBoostInferenceError, match="model metadata not found"):
        predict_with_artifact(X, str(path))
