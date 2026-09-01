import numpy as np
import pandas as pd
import pytest

from backend.app.services.ml_trading import predictions_to_long_only_signals, purged_walk_forward_predictions


def test_predictions_map_to_long_or_flat_signals():
    predictions = pd.Series([0, 1, 1, 0], index=pd.date_range("2025-01-01", periods=4))
    assert predictions_to_long_only_signals(predictions).tolist() == [-1, 1, 1, -1]


def test_predictions_reject_invalid_classes():
    predictions = pd.Series([0, 2])
    with pytest.raises(ValueError, match="only 0 or 1"):
        predictions_to_long_only_signals(predictions)


def test_walk_forward_predictions_are_out_of_sample_and_non_overlapping():
    rng = np.random.default_rng(42)
    n = 900
    returns = rng.normal(0.0003, 0.012, n)
    close = 50 * np.exp(np.cumsum(returns))
    frame = pd.DataFrame(
        {
            "Open": close * (1 + rng.normal(0, 0.002, n)),
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": rng.integers(100_000, 1_000_000, n),
        },
        index=pd.date_range("2022-01-01", periods=n, freq="D"),
    )
    run = purged_walk_forward_predictions(frame, train_size=300, test_size=100, step=100)
    assert run.folds > 0
    assert len(run.predictions) == run.test_rows
    assert not run.predictions.index.has_duplicates
    assert run.predictions.index.min() > frame.index[0]
    assert run.predictions.index.max() < frame.index[-1]
    assert run.predictions.isin([0, 1]).all()
    assert np.isfinite(run.probabilities.to_numpy()).all()
