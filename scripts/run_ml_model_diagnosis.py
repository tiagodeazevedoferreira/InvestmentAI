from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import average_precision_score, roc_auc_score

from app.services.ci_market_data import (
    CI_SYMBOLS,
    load_market_history,
)
from app.services.features import build_features
from app.services.xgboost_oos import (
    purged_xgboost_oos_predictions,
)


SYMBOLS = CI_SYMBOLS

START = "2021-01-01"
END = "2026-09-01"

HORIZON = 5
TRAIN_SIZE = 500
TEST_SIZE = 100
STEP = 100

SMD_DRIFT_THRESHOLD = 0.50

OUTPUT_PATH = Path(
    "artifacts/ml-model-diagnosis.json"
)


def _quantiles(
    values: pd.Series,
) -> dict[str, float | None]:
    clean = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return {
            "p05": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
        }

    quantile_values = clean.quantile(
        [0.05, 0.25, 0.50, 0.75, 0.95]
    )

    return {
        "p05": float(
            quantile_values.loc[0.05]
        ),
        "p25": float(
            quantile_values.loc[0.25]
        ),
        "p50": float(
            quantile_values.loc[0.50]
        ),
        "p75": float(
            quantile_values.loc[0.75]
        ),
        "p95": float(
            quantile_values.loc[0.95]
        ),
    }


def _brier_score(
    probabilities: pd.Series,
    target: pd.Series,
) -> float:
    aligned_probability, aligned_target = (
        probabilities.align(
            target,
            join="inner",
        )
    )

    if aligned_probability.empty:
        raise ValueError(
            "cannot calculate Brier score on empty data"
        )

    return float(
        np.mean(
            (
                aligned_probability.astype(float)
                - aligned_target.astype(float)
            )
            ** 2
        )
    )


def _calibration_buckets(
    probabilities: pd.Series,
    target: pd.Series,
) -> list[dict]:
    aligned_probability, aligned_target = (
        probabilities.align(
            target,
            join="inner",
        )
    )

    if aligned_probability.empty:
        return []

    frame = pd.DataFrame(
        {
            "probability": aligned_probability.astype(
                float
            ),
            "target": aligned_target.astype(int),
        }
    )

    bins = [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ]

    frame["bucket"] = pd.cut(
        frame["probability"],
        bins=bins,
        include_lowest=True,
        right=True,
    )

    rows: list[dict] = []

    for bucket, group in frame.groupby(
        "bucket",
        observed=False,
    ):
        if group.empty:
            continue

        rows.append(
            {
                "bucket": str(bucket),
                "rows": int(len(group)),
                "mean_probability": float(
                    group["probability"].mean()
                ),
                "observed_positive_rate": float(
                    group["target"].mean()
                ),
            }
        )

    return rows


def _normalize_ohlcv_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize provider OHLCV column names into the
    canonical schema used by the diagnosis pipeline.
    """

    rename_map: dict[str, str] = {}

    aliases = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "tick_volume": "volume",
        "real_volume": "volume",
    }

    for column in frame.columns:
        normalized = str(column).strip().lower()

        if normalized in aliases:
            rename_map[column] = aliases[
                normalized
            ]

    normalized_frame = frame.rename(
        columns=rename_map
    ).copy()

    required = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing = sorted(
        required
        - set(normalized_frame.columns)
    )

    if missing:
        raise ValueError(
            "missing required OHLCV columns after "
            "normalization: "
            + ", ".join(missing)
        )

    return normalized_frame


def _feature_drift(
    features: pd.DataFrame,
    fold_metadata,
) -> dict:
    """
    Compare every OOS test window with the training
    window belonging to the same walk-forward fold.

    abs_smd:
        absolute standardized mean difference.

    std_ratio:
        OOS standard deviation / training standard
        deviation.

    The drift statistics are diagnostic and are not
    used as a model-selection criterion.
    """

    feature_names = list(
        features.columns
    )

    fold_rows: list[dict] = []

    for fold in fold_metadata:
        train = features.loc[
            fold.train_start:fold.train_end,
            feature_names,
        ]

        test = features.loc[
            fold.test_start:fold.test_end,
            feature_names,
        ]

        if train.empty:
            raise ValueError(
                f"empty training window for fold "
                f"{fold.fold}"
            )

        if test.empty:
            raise ValueError(
                f"empty OOS test window for fold "
                f"{fold.fold}"
            )

        for feature in feature_names:
            train_values = pd.to_numeric(
                train[feature],
                errors="coerce",
            ).dropna()

            test_values = pd.to_numeric(
                test[feature],
                errors="coerce",
            ).dropna()

            if train_values.empty:
                raise ValueError(
                    f"empty training feature values "
                    f"for fold {fold.fold}, "
                    f"feature {feature}"
                )

            if test_values.empty:
                raise ValueError(
                    f"empty OOS feature values "
                    f"for fold {fold.fold}, "
                    f"feature {feature}"
                )

            train_mean = float(
                train_values.mean()
            )

            test_mean = float(
                test_values.mean()
            )

            train_std = float(
                train_values.std(
                    ddof=0
                )
            )

            test_std = float(
                test_values.std(
                    ddof=0
                )
            )

            if train_std > 0:
                abs_smd = (
                    abs(
                        test_mean
                        - train_mean
                    )
                    / train_std
                )

                std_ratio = (
                    test_std
                    / train_std
                )
            else:
                abs_smd = None
                std_ratio = None

            fold_rows.append(
                {
                    "fold": int(
                        fold.fold
                    ),
                    "train_start": (
                        fold.train_start.isoformat()
                    ),
                    "train_end": (
                        fold.train_end.isoformat()
                    ),
                    "test_start": (
                        fold.test_start.isoformat()
                    ),
                    "test_end": (
                        fold.test_end.isoformat()
                    ),
                    "feature": feature,
                    "train_rows": int(
                        len(train_values)
                    ),
                    "test_rows": int(
                        len(test_values)
                    ),
                    "train_mean": train_mean,
                    "oos_mean": test_mean,
                    "train_std": train_std,
                    "oos_std": test_std,
                    "abs_smd": abs_smd,
                    "std_ratio": std_ratio,
                }
            )

    summary: list[dict] = []

    for feature in feature_names:
        feature_rows = [
            row
            for row in fold_rows
            if row["feature"] == feature
        ]

        valid_smd = [
            row["abs_smd"]
            for row in feature_rows
            if row["abs_smd"] is not None
        ]

        valid_std_ratio = [
            row["std_ratio"]
            for row in feature_rows
            if row["std_ratio"] is not None
        ]

        summary.append(
            {
                "feature": feature,
                "folds": int(
                    len(feature_rows)
                ),
                "folds_with_abs_smd_ge_0_50": int(
                    sum(
                        value
                        >= SMD_DRIFT_THRESHOLD
                        for value in valid_smd
                    )
                ),
                "mean_abs_smd": (
                    float(
                        np.mean(valid_smd)
                    )
                    if valid_smd
                    else None
                ),
                "max_abs_smd": (
                    float(
                        np.max(valid_smd)
                    )
                    if valid_smd
                    else None
                ),
                "mean_std_ratio": (
                    float(
                        np.mean(
                            valid_std_ratio
                        )
                    )
                    if valid_std_ratio
                    else None
                ),
                "min_std_ratio": (
                    float(
                        np.min(
                            valid_std_ratio
                        )
                    )
                    if valid_std_ratio
                    else None
                ),
                "max_std_ratio": (
                    float(
                        np.max(
                            valid_std_ratio
                        )
                    )
                    if valid_std_ratio
                    else None
                ),
            }
        )

    summary.sort(
        key=lambda row: (
            row["mean_abs_smd"]
            if row["mean_abs_smd"]
            is not None
            else -1
        ),
        reverse=True,
    )

    return {
        "threshold_abs_smd": (
            SMD_DRIFT_THRESHOLD
        ),
        "reference": (
            "Each OOS test window is compared "
            "against the training window of the "
            "same walk-forward fold."
        ),
        "summary": summary,
        "folds": fold_rows,
    }


def _fold_performance(
    probabilities: pd.Series,
    target: pd.Series,
    fold_metadata,
) -> list[dict]:
    """
    Measure OOS predictive performance for each
    walk-forward fold.

    Each fold is evaluated only on its own OOS
    test interval.
    """

    rows: list[dict] = []

    for fold in fold_metadata:
        fold_probabilities = probabilities.loc[
            fold.test_start:fold.test_end
        ]

        fold_target = target.loc[
            fold.test_start:fold.test_end
        ]

        if fold_probabilities.empty:
            raise ValueError(
                f"empty OOS probability window "
                f"for fold {fold.fold}"
            )

        if fold_target.empty:
            raise ValueError(
                f"empty OOS target window "
                f"for fold {fold.fold}"
            )

        fold_target = fold_target.reindex(
            fold_probabilities.index
        )

        if fold_target.isna().any():
            raise ValueError(
                f"target alignment produced NaN "
                f"values for fold {fold.fold}"
            )

        predictions = (
            fold_probabilities
            .ge(0.5)
            .astype(int)
        )

        actual = fold_target.astype(int)

        has_both_classes = (
            actual.nunique() == 2
        )

        rows.append(
            {
                "fold": int(
                    fold.fold
                ),
                "test_start": (
                    fold.test_start.isoformat()
                ),
                "test_end": (
                    fold.test_end.isoformat()
                ),
                "rows": int(
                    len(actual)
                ),
                "actual_positive_rate": float(
                    actual.mean()
                ),
                "predicted_positive_rate": float(
                    predictions.mean()
                ),
                "mean_probability": float(
                    fold_probabilities.mean()
                ),
                "accuracy": float(
                    predictions.eq(
                        actual
                    ).mean()
                ),
                "brier_score": _brier_score(
                    fold_probabilities,
                    actual,
                ),
                "roc_auc": (
                    float(
                        roc_auc_score(
                            actual,
                            fold_probabilities,
                        )
                    )
                    if has_both_classes
                    else None
                ),
                "pr_auc": (
                    float(
                        average_precision_score(
                            actual,
                            fold_probabilities,
                        )
                    )
                    if has_both_classes
                    else None
                ),
            }
        )

    return rows


def _yearly_metrics(
    probabilities: pd.Series,
    target: pd.Series,
) -> list[dict]:
    aligned_probability, aligned_target = (
        probabilities.align(
            target,
            join="inner",
        )
    )

    if aligned_probability.empty:
        return []

    predictions = (
        aligned_probability
        .ge(0.5)
        .astype(int)
    )

    frame = pd.DataFrame(
        {
            "probability": (
                aligned_probability
            ),
            "target": (
                aligned_target.astype(int)
            ),
            "prediction": predictions,
        }
    )

    frame["year"] = frame.index.year

    rows: list[dict] = []

    for year, group in frame.groupby(
        "year",
        sort=True,
    ):
        rows.append(
            {
                "year": int(year),
                "rows": int(
                    len(group)
                ),
                "actual_positive_rate": float(
                    group["target"].mean()
                ),
                "predicted_positive_rate": float(
                    group["prediction"].mean()
                ),
                "mean_probability": float(
                    group["probability"].mean()
                ),
                "accuracy": float(
                    group["prediction"]
                    .eq(
                        group["target"]
                    )
                    .mean()
                ),
                "brier_score": _brier_score(
                    group["probability"],
                    group["target"],
                ),
            }
        )

    return rows


def diagnose_symbol(
    symbol: str,
    source: str,
) -> dict:
    market, quality = load_market_history(
        symbol=symbol,
        source=source,
        start=START,
        end=END,
        interval="1d",
    )

    market = _normalize_ohlcv_columns(
        market
    )

    features, target = build_features(
        market,
        horizon=HORIZON,
    )

    prediction_run = (
        purged_xgboost_oos_predictions(
            features,
            target,
            horizon=HORIZON,
            train_size=TRAIN_SIZE,
            test_size=TEST_SIZE,
            step=STEP,
        )
    )

    probabilities = (
        prediction_run.probabilities.copy()
    )

    target_eval = target.reindex(
        probabilities.index
    )

    if target_eval.isna().any():
        raise ValueError(
            f"target alignment produced NaN "
            f"values for {symbol}"
        )

    predictions = (
        probabilities
        .ge(0.5)
        .astype(int)
    )

    actual = target_eval.astype(int)

    correctness = predictions.eq(
        actual
    )

    feature_stats: list[dict] = []

    for feature in features.columns:
        feature_values = features.loc[
            probabilities.index,
            feature,
        ]

        feature_stats.append(
            {
                "feature": feature,
                "rows": int(
                    feature_values.notna().sum()
                ),
                "mean": float(
                    feature_values.mean()
                ),
                "std": float(
                    feature_values.std(
                        ddof=0
                    )
                ),
                "quantiles": _quantiles(
                    feature_values
                ),
            }
        )

    feature_drift = _feature_drift(
        features,
        prediction_run.fold_metadata,
    )

    fold_performance = _fold_performance(
        probabilities,
        target_eval,
        prediction_run.fold_metadata,
    )

    yearly_metrics = _yearly_metrics(
        probabilities,
        target_eval,
    )

    return {
        "symbol": symbol,
        "source": source,
        "quality": (
            quality.model_dump()
            if quality is not None
            and hasattr(
                quality,
                "model_dump",
            )
            else (
                quality.__dict__
                if quality is not None
                else None
            )
        ),
        "protocol": {
            "model": "xgboost",
            "horizon": HORIZON,
            "train_size": TRAIN_SIZE,
            "test_size": TEST_SIZE,
            "step": STEP,
            "walk_forward": True,
            "purged": True,
            "threshold": 0.5,
        },
        "rows": {
            "features": int(
                len(features)
            ),
            "target": int(
                len(target)
            ),
            "oos_predictions": int(
                prediction_run.test_rows
            ),
            "oos_folds": int(
                prediction_run.folds
            ),
        },
        "metrics": {
            "accuracy": float(
                correctness.mean()
            ),
            "brier_score": _brier_score(
                probabilities,
                actual,
            ),
            "actual_positive_rate": float(
                actual.mean()
            ),
            "predicted_positive_rate": float(
                predictions.mean()
            ),
            "mean_probability": float(
                probabilities.mean()
            ),
        },
        "calibration": _calibration_buckets(
            probabilities,
            actual,
        ),
        "yearly_metrics": yearly_metrics,
        "feature_stats": feature_stats,
        "feature_drift": feature_drift,
        "fold_performance": fold_performance,
        "fold_metadata": [
            {
                "fold": int(
                    fold.fold
                ),
                "train_start": (
                    fold.train_start.isoformat()
                ),
                "train_end": (
                    fold.train_end.isoformat()
                ),
                "test_start": (
                    fold.test_start.isoformat()
                ),
                "test_end": (
                    fold.test_end.isoformat()
                ),
            }
            for fold in (
                prediction_run.fold_metadata
            )
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose XGBoost OOS model "
            "performance, calibration and "
            "feature drift."
        )
    )

    parser.add_argument(
        "--source",
        default="fixture",
        choices=[
            "fixture",
            "provider",
        ],
        help=(
            "Market data source used for "
            "the diagnosis."
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            OUTPUT_PATH
        ),
        help="Output JSON path.",
    )

    args = parser.parse_args()

    reports: list[dict] = []

    for symbol in SYMBOLS:
        print(
            f"[diagnosis] {symbol} "
            f"source={args.source}"
        )

        report = diagnose_symbol(
            symbol=symbol,
            source=args.source,
        )

        reports.append(
            report
        )

        metrics = report[
            "metrics"
        ]

        print(
            f"  accuracy="
            f"{metrics['accuracy']:.4f} "
            f"brier="
            f"{metrics['brier_score']:.4f} "
            f"rows="
            f"{report['rows']['oos_predictions']} "
            f"folds="
            f"{report['rows']['oos_folds']}"
        )

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            reports,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"[diagnosis] written to "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()
