from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services.features import build_features
from app.services.ml_cross_asset import purged_cross_asset_walk_forward_predictions
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


def _brier(probability: pd.Series, target: pd.Series) -> float:
    return float(((probability - target.astype(float)) ** 2).mean())


def _ece(probability: pd.Series, target: pd.Series, bins: int = 10) -> float:
    bucket = pd.cut(
        probability,
        bins=[i / bins for i in range(bins + 1)],
        include_lowest=True,
    )
    total = len(target)
    error = 0.0
    for _, group in target.groupby(bucket, observed=True):
        if len(group) == 0:
            continue
        p = probability.loc[group.index]
        error += len(group) / total * abs(float(p.mean()) - float(group.mean()))
    return float(error)


def _evaluate(symbol: str, frame: pd.DataFrame, pooled_probability: pd.Series) -> dict:
    baseline = purged_walk_forward_predictions(
        frame.rename(columns=str.title),
        horizon=HORIZON,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
        step=STEP,
    )
    if not baseline.probabilities.index.equals(pooled_probability.index):
        raise ValueError(f"baseline and pooled test windows differ for {symbol}")

    _, target = build_features(frame.rename(columns=str.title), horizon=HORIZON)
    target = target.reindex(pooled_probability.index)

    fold_brier_baseline: list[float] = []
    fold_brier_pooled: list[float] = []
    fold_ece_baseline: list[float] = []
    fold_ece_pooled: list[float] = []
    for start in range(0, len(target), TEST_SIZE):
        target_fold = target.iloc[start : start + TEST_SIZE]
        if len(target_fold) != TEST_SIZE:
            break
        base_prob = baseline.probabilities.iloc[start : start + TEST_SIZE]
        pooled_prob = pooled_probability.iloc[start : start + TEST_SIZE]
        fold_brier_baseline.append(_brier(base_prob, target_fold))
        fold_brier_pooled.append(_brier(pooled_prob, target_fold))
        fold_ece_baseline.append(_ece(base_prob, target_fold))
        fold_ece_pooled.append(_ece(pooled_prob, target_fold))

    return {
        "symbol": symbol,
        "baseline": {
            "folds": baseline.folds,
            "prediction_rows": baseline.test_rows,
            "brier_by_fold": fold_brier_baseline,
            "ece_by_fold": fold_ece_baseline,
            "brier_mean": _brier(baseline.probabilities, target),
            "ece_mean": _ece(baseline.probabilities, target),
        },
        "pooled": {
            "folds": len(fold_brier_pooled),
            "prediction_rows": len(pooled_probability),
            "brier_by_fold": fold_brier_pooled,
            "ece_by_fold": fold_ece_pooled,
            "brier_mean": _brier(pooled_probability, target),
            "ece_mean": _ece(pooled_probability, target),
        },
        "paired_statistics": [
            paired_fold_summary(
                fold_brier_baseline,
                fold_brier_pooled,
                metric="brier",
                comparison="pooled_vs_asset_specific",
            ).__dict__,
            paired_fold_summary(
                fold_ece_baseline,
                fold_ece_pooled,
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
        _evaluate(symbol, frames[symbol], pooled.by_symbol[symbol].probabilities)
        for symbol in SYMBOLS
    ]
    output = Path("artifacts/ml-cross-asset-experiment.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
