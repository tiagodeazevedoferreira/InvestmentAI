from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.services.features import build_features
from app.services.ml_trading import purged_walk_forward_predictions
from app.services.openbb_market_data import OpenBBMarketDataProvider

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
START = "2021-01-01"
END = "2026-09-01"
HORIZON = 5


def _quantiles(values: pd.Series) -> dict[str, float]:
    return {
        "p05": float(values.quantile(0.05)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p95": float(values.quantile(0.95)),
    }


def _brier_score(probabilities: pd.Series, target: pd.Series) -> float:
    return float(((probabilities - target.astype(float)) ** 2).mean())


def _calibration_buckets(probabilities: pd.Series, target: pd.Series) -> list[dict]:
    bins = pd.cut(
        probabilities,
        bins=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        include_lowest=True,
    )
    rows: list[dict] = []
    for bucket, group in target.groupby(bins, observed=True):
        if len(group) == 0:
            continue
        p = probabilities.loc[group.index]
        rows.append(
            {
                "bucket": str(bucket),
                "rows": int(len(group)),
                "mean_probability": float(p.mean()),
                "observed_positive_rate": float(group.mean()),
            }
        )
    return rows


def diagnose_symbol(provider: OpenBBMarketDataProvider, symbol: str) -> dict:
    frame, quality = provider.historical_with_quality(symbol, start=START, end=END, interval="1d")
    features, target = build_features(frame.rename(columns=str.title), horizon=HORIZON)
    prediction_run = purged_walk_forward_predictions(frame.rename(columns=str.title), horizon=HORIZON)

    probabilities = prediction_run.probabilities.copy()
    target_eval = target.reindex(probabilities.index)
    features_eval = features.reindex(probabilities.index)
    if target_eval.isna().any():
        raise ValueError(f"target alignment produced NaN values for {symbol}")
    if features_eval.isna().any().any():
        raise ValueError(f"feature alignment produced NaN values for {symbol}")

    predictions = probabilities.ge(0.5).astype(int)
    actual = target_eval.astype(int)
    correct = predictions.eq(actual)

    feature_stats = {}
    for column in features_eval.columns:
        series = features_eval[column].astype(float)
        feature_stats[column] = {
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
            "median": float(series.median()),
        }

    yearly = []
    for year, group in actual.groupby(actual.index.year):
        p = probabilities.loc[group.index]
        pred = predictions.loc[group.index]
        yearly.append(
            {
                "year": int(year),
                "rows": int(len(group)),
                "actual_positive_rate": float(group.mean()),
                "predicted_positive_rate": float(pred.mean()),
                "mean_probability": float(p.mean()),
                "accuracy": float(pred.eq(group).mean()),
                "brier_score": _brier_score(p, group),
            }
        )

    return {
        "symbol": symbol,
        "rows": quality.rows,
        "prediction_rows": prediction_run.test_rows,
        "folds": prediction_run.folds,
        "evaluation_start": probabilities.index[0].isoformat(),
        "evaluation_end": probabilities.index[-1].isoformat(),
        "target_positive_rate": float(actual.mean()),
        "predicted_positive_rate_at_0_50": float(predictions.mean()),
        "mean_probability": float(probabilities.mean()),
        "probability_std": float(probabilities.std(ddof=0)),
        "probability_quantiles": _quantiles(probabilities),
        "accuracy_at_0_50": float(correct.mean()),
        "brier_score": _brier_score(probabilities, actual),
        "calibration_buckets": _calibration_buckets(probabilities, actual),
        "yearly": yearly,
        "feature_stats": feature_stats,
    }


def main() -> None:
    provider = OpenBBMarketDataProvider()
    reports = [diagnose_symbol(provider, symbol) for symbol in SYMBOLS]
    output = Path("artifacts/ml-model-diagnosis.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
