import numpy as np
import pandas as pd

from app.services import ml_cross_asset


def _frame(rows: int = 80) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=rows, freq="D")
    base = np.linspace(100.0, 130.0, rows)
    return pd.DataFrame(
        {
            "Open": base,
            "High": base + 1.0,
            "Low": base - 1.0,
            "Close": base + np.sin(np.arange(rows) / 3.0),
            "Volume": np.linspace(1_000_000, 1_100_000, rows),
        },
        index=index,
    )


def test_cross_asset_predictions_are_produced_for_each_symbol() -> None:
    result = ml_cross_asset.purged_cross_asset_walk_forward_predictions(
        {"AAA": _frame(), "BBB": _frame()},
        horizon=3,
        train_size=20,
        test_size=10,
        step=10,
    )

    assert set(result.by_symbol) == {"AAA", "BBB"}
    for run in result.by_symbol.values():
        assert run.test_rows == len(run.predictions) == len(run.probabilities)
        assert run.folds > 0
        assert np.isfinite(run.probabilities.to_numpy()).all()


def test_training_window_is_causal_for_target_fold(monkeypatch) -> None:
    captured: list[pd.Index] = []

    class FakeModel:
        def fit(self, X, y):
            captured.append(X.index.copy())
            return self

        def predict(self, X):
            return np.zeros(len(X), dtype=int)

        def predict_proba(self, X):
            return np.column_stack([np.full(len(X), 0.4), np.full(len(X), 0.6)])

    monkeypatch.setattr(ml_cross_asset, "_model", lambda: FakeModel())
    ml_cross_asset.purged_cross_asset_walk_forward_predictions(
        {"AAA": _frame(), "BBB": _frame()},
        horizon=3,
        train_size=20,
        test_size=10,
        step=10,
    )

    assert captured
    # The first fold tests after train_size + horizon observations. Training
    # contains only observations strictly before that test boundary.
    first_cutoff = pd.date_range("2020-01-01", periods=20 + 3 + 1, freq="D")[-1]
    assert max(captured[0]) < first_cutoff
    assert len(captured[0]) == 40
