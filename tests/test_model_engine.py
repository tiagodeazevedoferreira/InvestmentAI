import json

import numpy as np
import pandas as pd

from backend.app.services.evaluation import classification_metrics
from backend.app.services.model_engine import predict_xgboost, train_xgboost


def test_classification_metrics_include_accuracy_precision_recall_and_roc_auc():
    y_true = pd.Series([0, 0, 1, 1])
    probability = np.array([0.10, 0.40, 0.60, 0.90])

    metrics = classification_metrics(y_true, probability)

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["samples"] == 4


def test_train_xgboost_saves_model_and_metadata(tmp_path):
    rng = np.random.default_rng(42)
    n = 200

    X = pd.DataFrame(
        {
            "feature_a": rng.normal(size=n),
            "feature_b": rng.normal(size=n),
        }
    )
    y = pd.Series((X["feature_a"] + X["feature_b"] > 0).astype(int))

    model_path = tmp_path / "baseline.json"

    metadata = train_xgboost(
        X,
        y,
        str(model_path),
        params={
            "n_estimators": 20,
            "max_depth": 2,
        },
    )

    assert model_path.exists()
    assert model_path.with_suffix(".meta.json").exists()

    assert metadata["feature_version"] == "technical-v1"
    assert metadata["features"] == ["feature_a", "feature_b"]

    metrics = metadata["metrics"]
    assert set(
        ["accuracy", "precision", "recall", "roc_auc", "samples"]
    ).issubset(metrics)

    saved_metadata = json.loads(
        model_path.with_suffix(".meta.json").read_text(encoding="utf-8")
    )
    assert saved_metadata["features"] == ["feature_a", "feature_b"]


def test_predict_xgboost_returns_probability_between_zero_and_one(tmp_path):
    rng = np.random.default_rng(7)
    n = 200

    X = pd.DataFrame(
        {
            "feature_a": rng.normal(size=n),
            "feature_b": rng.normal(size=n),
        }
    )
    y = pd.Series((X["feature_a"] > 0).astype(int))

    model_path = tmp_path / "baseline.json"

    train_xgboost(
        X,
        y,
        str(model_path),
        params={
            "n_estimators": 20,
            "max_depth": 2,
        },
    )

    probability = predict_xgboost(X.iloc[[0]], str(model_path))

    assert 0.0 <= probability <= 1.0
