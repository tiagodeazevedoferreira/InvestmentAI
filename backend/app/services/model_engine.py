from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from .features import chronological_split
from .evaluation import classification_metrics

FEATURE_VERSION = "technical-v1"


def train_xgboost(X, y, model_path: str, params: dict | None = None) -> dict:
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("xgboost is not installed") from exc
    if len(X) < 100:
        raise ValueError("at least 100 samples are required for training")
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = chronological_split(X, y)
    if y_train.nunique() < 2:
        raise ValueError("training labels contain only one class")
    cfg = {"n_estimators": 300, "max_depth": 4, "learning_rate": .05, "subsample": .8, "colsample_bytree": .8, "random_state": 42, "eval_metric": "logloss"}
    cfg.update(params or {})
    model = XGBClassifier(**cfg)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    probability = model.predict_proba(X_test)[:, 1]
    metrics = classification_metrics(y_test, probability)
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(path)
    metadata = {"feature_version": FEATURE_VERSION, "features": list(X.columns), "params": cfg, "metrics": metrics, "model_path": str(path)}
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def predict_xgboost(X, model_path: str) -> float:
    from xgboost import XGBClassifier
    model = XGBClassifier()
    model.load_model(model_path)
    return float(model.predict_proba(X)[:, 1][-1])
