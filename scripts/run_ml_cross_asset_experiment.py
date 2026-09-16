from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.features import build_features
from app.services.ml_cross_asset import purged_cross_asset_walk_forward_predictions
from app.services.ml_cross_asset_diagnostics import (
    diagnose_predictions,
    feature_distribution_shift,
)
from app.services.ml_trading import purged_walk_forward_predictions
from app.services.openbb_market_data import OpenBBMarketDataProvider
from app.services.probability_evaluation import paired_fold_summary

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
START = "2021-01-01"
END = "2026-09-01"
HORIZON = 5
TRAIN_SIZE = 500
TEST_SIZE = 100
STEP = 100


def _fold_metrics(
    probability: pd.Series,
    target: pd.Series,
) -> tuple[list[float], list[float]]:
    brier: list[float] = []
    ece: list[float] = []
    for start in range(0, len(probability), TEST_SIZE):
        probability_fold = probability.iloc[start : start + TEST_SIZE]
        target_fold = target.iloc[start : start + TEST_SIZE]
        if len(probability_fold) != TEST_SIZE or len(target_fold) != TEST_SIZE:
            break
        diagnostics = diagnose_predictions(probability_fold, target_fold)
        brier.append(diagnostics.brier)
        ece.append(diagnostics.ece)
    return brier, ece


def _evaluate(symbol: str, frame: pd.DataFrame, pooled_run) -> dict:
    baseline = purged_walk_forward_predictions(
        frame.rename(columns=str.title),
        horizon=HORIZON,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
        step=STEP,
    )
    pooled_probability = pooled_run.probabilities
    pooled_prediction = pooled_run.predictions
    if not baseline.probabilities.index.equals(pooled_probability.index):
        raise ValueError(f"baseline and pooled test windows differ for {symbol}")

    features, target = build_features(frame.rename(columns=str.title), horizon=HORIZON)
    target = target.reindex(pooled_probability.index)

    baseline_brier, baseline_ece = _fold_metrics(baseline.probabilities, target)
    pooled_brier, pooled_ece = _fold_metrics(pooled_probability, target)

    first_oos = pooled_probability.index.min()
    reference = features.loc[features.index < first_oos].tail(TRAIN_SIZE)
    observed = features.loc[pooled_probability.index]

    return {
        "symbol": symbol,
        "baseline": {
            "folds": baseline.folds,
            "prediction_rows": baseline.test_rows,
            "brier_by_fold": baseline_brier,
            "ece_by_fold": baseline_ece,
            "diagnostics": diagnose_predictions(
                baseline.probabilities,
                target,
                prediction=baseline.predictions,
                fold_brier=baseline_brier,
                fold_ece=baseline_ece,
            ).to_dict(),
        },
        "pooled": {
            "folds": pooled_run.folds,
            "prediction_rows": pooled_run.test_rows,
            "brier_by_fold": pooled_brier,
            "ece_by_fold": pooled_ece,
            "diagnostics": diagnose_predictions(
                pooled_probability,
                target,
                prediction=pooled_prediction,
                fold_brier=pooled_brier,
                fold_ece=pooled_ece,
            ).to_dict(),
        },
        "feature_distribution_shift": feature_distribution_shift(reference, observed),
        "paired_statistics": [
            paired_fold_summary(
                baseline_brier,
                pooled_brier,
                metric="brier",
                comparison="pooled_vs_asset_specific",
            ).__dict__,
            paired_fold_summary(
                baseline_ece,
                pooled_ece,
                metric="ece",
                comparison="pooled_vs_asset_specific",
            ).__dict__,
        ],
    }


def main() -> None:
    provider = OpenBBMarketDataProvider()
    frames = {
        symbol: provider.historical_with_quality(symbol, start=START, end=END, interval="1d")[0]
        for symbol in SYMBOLS
    }
    pooled = purged_cross_asset_walk_forward_predictions(
        {symbol: frame.rename(columns=str.title) for symbol, frame in frames.items()},
        horizon=HORIZON,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
        step=STEP,
    )

    reports = [
        _evaluate(symbol, frames[symbol], pooled.by_symbol[symbol])
        for symbol in SYMBOLS
    ]
    output = Path("artifacts/ml-cross-asset-experiment.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
