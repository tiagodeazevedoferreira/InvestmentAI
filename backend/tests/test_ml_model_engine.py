from __future__ import annotations

import numpy as np
import pandas as pd

from app.services import model_engine


def test_train_xgboost_uses_five_bar_purge(monkeypatch, tmp_path) -> None:
    X = pd.DataFrame({"feature": range(100)})
    y = pd.Series([0, 1] * 50)

    captured: dict[str, int] = {}

    def fake_split(X, y, **kwargs):
        captured["purge_bars"] = kwargs["purge_bars"]
        return (
            X.iloc[:65],
            y.iloc[:65],
        ), (
            X.iloc[70:80],
            y.iloc[70:80],
        ), (
            X.iloc[85:],
            y.iloc[85:],
        )

    monkeypatch.setattr(model_engine, "chronological_split", fake_split)

    class FakeModel:
        def __init__(self, **kwargs):
            self.params = kwargs

        def fit(self, X_train, y_train, eval_set=None, verbose=False):
            assert len(X_train) == 65
            assert len(y_train) == 65
            assert len(eval_set[0][0]) == 10
            assert len(eval_set[0][1]) == 10

        def predict_proba(self, X_test):
            return np.array([[0.4, 0.6] for _ in range(len(X_test))])

        def save_model(self, path):
            path.write_text("fake-model", encoding="utf-8")

    class FakeXGBoost:
        XGBClassifier = FakeModel

    monkeypatch.setitem(__import__("sys").modules, "xgboost", FakeXGBoost())

    monkeypatch.setattr(
        model_engine,
        "classification_metrics",
        lambda y_true, probability: {"accuracy": 1.0},
    )

    result = model_engine.train_xgboost(
        X,
        y,
        str(tmp_path / "model.json"),
    )

    assert captured["purge_bars"] == 5
    assert result["metrics"] == {"accuracy": 1.0}
