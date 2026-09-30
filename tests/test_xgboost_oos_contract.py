import numpy as np
import pandas as pd

from app.services.xgboost_oos import purged_xgboost_oos_predictions


def test_xgboost_oos_returns_fold_metadata():
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

    result = purged_xgboost_oos_predictions(
        X,
        y,
        horizon=5,
        train_size=500,
        test_size=100,
        step=100,
    )

    assert result.folds == len(result.fold_metadata)
    assert result.folds > 0
    assert result.test_rows == len(result.probabilities)
    assert result.test_rows == len(result.predictions)

    for fold in result.fold_metadata:
        assert fold.train_start <= fold.train_end
        assert fold.test_start <= fold.test_end
        assert fold.train_end < fold.test_start

    for previous, current in zip(
        result.fold_metadata,
        result.fold_metadata[1:],
    ):
        assert previous.test_end < current.test_start
