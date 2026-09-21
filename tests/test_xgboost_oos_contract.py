import numpy as np
import pandas as pd

from app.services.xgboost_oos import purged_xgboost_oos_predictions


def test_xgboost_oos_returns_non_overlapping_fold_metadata():
    index = pd.date_range("2020-01-01", periods=900, freq="D")
    X = pd.DataFrame(
        {
            "feature_1": np.sin(np.arange(900) / 20.0),
            "feature_2": np.cos(np.arange(900) / 30.0),
        },
        index=index,
    )
    y = pd.Series(
        (np.arange(900) % 2).astype(int),
        index=index,
        name="target",
    )

    horizon = 5
    train_size = 500
    test_size = 100
    step = 100

    result = purged_xgboost_oos_predictions(
        X,
        y,
        horizon=horizon,
        train_size=train_size,
        test_size=test_size,
        step=step,
    )

    assert result.folds == len(result.fold_metadata)
    assert result.folds > 0
    assert result.test_rows == len(result.probabilities)
    assert result.test_rows == len(result.predictions)

    for fold in result.fold_metadata:
        train_end_position = X.index.get_loc(fold.train_end)
        test_start_position = X.index.get_loc(fold.test_start)
        test_end_position = X.index.get_loc(fold.test_end)

        assert fold.train_start <= fold.train_end
        assert fold.test_start <= fold.test_end

        # train_end is the last row included in training. With a purge
        # horizon of N rows, the test window begins at the position after
        # those N intervening rows, hence a positional distance of N + 1.
        assert test_start_position - train_end_position == horizon + 1
        assert test_end_position - test_start_position + 1 == test_size

    for previous, current in zip(result.fold_metadata, result.fold_metadata[1:]):
        assert previous.test_end < current.test_start
