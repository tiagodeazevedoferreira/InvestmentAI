from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_features
from .ml_trading import MLPredictionRun


@dataclass(frozen=True)
class CrossAssetPredictionRun:
    by_symbol: dict[str, MLPredictionRun]


def _model() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def purged_cross_asset_walk_forward_predictions(
    frames: dict[str, pd.DataFrame],
    *,
    horizon: int = 5,
    train_size: int = 500,
    test_size: int = 100,
    step: int = 100,
) -> CrossAssetPredictionRun:
    """Evaluate one shared model across assets with causal per-asset windows.

    For each asset, test windows follow the single-asset walk-forward schedule.
    Each fold trains one shared model using the latest ``train_size`` observations
    from every asset that are strictly before the target fold's purge boundary.
    The target asset therefore has the same train/purge/test geometry as the
    existing single-asset baseline.

    Features and future targets are built independently per asset, so rolling
    indicators and labels never cross asset boundaries. The shared model receives
    only normalized technical features and no asset identifier, making this a
    transfer-learning experiment rather than an asset-specific model.
    """
    if not frames:
        raise ValueError("frames must contain at least one asset")
    if min(horizon, train_size, test_size, step) < 1:
        raise ValueError("horizon, train_size, test_size and step must be positive")

    prepared: dict[str, tuple[pd.DataFrame, pd.Series]] = {}
    for symbol, frame in frames.items():
        if not symbol:
            raise ValueError("asset symbols must be non-empty")
        X, y = build_features(frame, horizon=horizon)
        if len(X) < train_size + horizon + test_size:
            raise ValueError(f"insufficient observations for {symbol}")
        prepared[symbol] = (X, y)

    output: dict[str, MLPredictionRun] = {}
    for target_symbol, (target_X, target_y) in prepared.items():
        predictions: list[pd.Series] = []
        probabilities: list[pd.Series] = []
        start = 0
        folds = 0

        while start + train_size + horizon + test_size <= len(target_X):
            train_end = start + train_size
            test_start = train_end + horizon
            test_end = test_start + test_size
            purge_boundary = target_X.index[train_end]
            test_X = target_X.iloc[test_start:test_end]

            train_parts_X: list[pd.DataFrame] = []
            train_parts_y: list[pd.Series] = []
            for asset_X, asset_y in prepared.values():
                eligible = asset_X.index < purge_boundary
                asset_X_before_cutoff = asset_X.loc[eligible]
                if len(asset_X_before_cutoff) < train_size:
                    continue
                selected_X = asset_X_before_cutoff.iloc[-train_size:]
                train_parts_X.append(selected_X)
                train_parts_y.append(asset_y.loc[selected_X.index])

            if not train_parts_X:
                start += step
                continue

            X_train = pd.concat(train_parts_X, axis=0)
            y_train = pd.concat(train_parts_y, axis=0)
            if y_train.nunique() < 2:
                start += step
                continue

            model = _model()
            model.fit(X_train, y_train)
            predictions.append(pd.Series(model.predict(test_X), index=test_X.index, name="prediction"))
            probabilities.append(
                pd.Series(model.predict_proba(test_X)[:, 1], index=test_X.index, name="probability")
            )
            folds += 1
            start += step

        if not predictions:
            raise ValueError(f"no valid cross-asset folds were produced for {target_symbol}")

        pred = pd.concat(predictions).sort_index()
        prob = pd.concat(probabilities).sort_index()
        if pred.index.has_duplicates:
            raise ValueError(f"cross-asset test windows overlap for {target_symbol}")
        if not np.isfinite(prob.to_numpy()).all():
            raise ValueError(f"non-finite cross-asset probabilities for {target_symbol}")
        if target_y.reindex(prob.index).isna().any():
            raise ValueError(f"target alignment failed for {target_symbol}")

        output[target_symbol] = MLPredictionRun(
            predictions=pred,
            probabilities=prob,
            test_rows=len(pred),
            folds=folds,
        )

    return CrossAssetPredictionRun(by_symbol=output)
