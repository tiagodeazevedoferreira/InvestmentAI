from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

SYMBOLS = ("PETR4", "VALE3", "ITUB4")
EXPECTED_FOLDS = 7
HORIZON = 5
THRESHOLD = 0.60


def _by_symbol(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol in result:
            raise ValueError(f"duplicate symbol: {symbol}")
        result[symbol] = row
    return result


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _fold_observations(observations: list[dict], fold: dict) -> list[dict]:
    start = _parse_timestamp(str(fold["test_start"]))
    end = _parse_timestamp(str(fold["test_end"]))
    selected = [
        item
        for item in observations
        if start <= _parse_timestamp(str(item["timestamp"])) <= end
    ]
    if len(selected) != 100:
        raise ValueError(
            f"fold {fold['fold']} expected 100 observations, got {len(selected)}"
        )
    return selected


def _fold_spread(observations: list[dict]) -> dict:
    long = np.array(
        [float(item["future_return_5d"]) for item in observations if item.get("regime") == "long"],
        dtype=float,
    )
    cash = np.array(
        [float(item["future_return_5d"]) for item in observations if item.get("regime") == "cash"],
        dtype=float,
    )
    if len(long) == 0 or len(cash) == 0:
        raise ValueError("each fold must contain both long and cash observations")
    return {
        "long_rows": int(len(long)),
        "cash_rows": int(len(cash)),
        "long_mean_future_return_5d": float(long.mean()),
        "cash_mean_future_return_5d": float(cash.mean()),
        "spread_long_minus_cash": float(long.mean() - cash.mean()),
    }


def _summary(rows: list[dict]) -> dict:
    values = np.array([float(row["spread_long_minus_cash"]) for row in rows], dtype=float)
    return {
        "folds": int(len(values)),
        "positive_spread_folds": int(np.sum(values > 0.0)),
        "negative_spread_folds": int(np.sum(values < 0.0)),
        "zero_spread_folds": int(np.sum(values == 0.0)),
        "positive_spread_fraction": float(np.mean(values > 0.0)),
        "mean_fold_spread": float(values.mean()),
        "median_fold_spread": float(np.median(values)),
        "min_fold_spread": float(values.min()),
        "max_fold_spread": float(values.max()),
        "std_fold_spread": float(values.std(ddof=0)),
        "all_folds_positive": bool(np.all(values > 0.0)),
    }


def evaluate(signal_diagnostics: list[dict], shared_artifacts: list[dict]) -> dict:
    signals = _by_symbol(signal_diagnostics)
    artifacts = _by_symbol(shared_artifacts)
    if set(signals) != set(SYMBOLS) or set(artifacts) != set(SYMBOLS):
        raise ValueError("reports must contain exactly PETR4, VALE3 and ITUB4")

    symbol_reports = []
    for symbol in SYMBOLS:
        signal = signals[symbol]
        artifact = artifacts[symbol]
        observations = signal.get("conditional_return_observations_5d")
        folds = artifact.get("fold_metadata")
        if not isinstance(observations, list):
            raise ValueError(f"{symbol}: missing conditional_return_observations_5d")
        if not isinstance(folds, list) or len(folds) != EXPECTED_FOLDS:
            raise ValueError(f"{symbol}: expected exactly {EXPECTED_FOLDS} fold metadata entries")

        fold_rows = []
        for fold in folds:
            selected = _fold_observations(observations, fold)
            metrics = _fold_spread(selected)
            fold_rows.append({
                "symbol": symbol,
                "fold": int(fold["fold"]),
                "train_start": str(fold["train_start"]),
                "train_end": str(fold["train_end"]),
                "test_start": str(fold["test_start"]),
                "test_end": str(fold["test_end"]),
                **metrics,
            })

        symbol_reports.append({
            "symbol": symbol,
            "threshold": THRESHOLD,
            "horizon": HORIZON,
            "folds": fold_rows,
            "summary": _summary(fold_rows),
        })

    all_rows = [row for report in symbol_reports for row in report["folds"]]
    all_values = np.array(
        [float(row["spread_long_minus_cash"]) for row in all_rows], dtype=float
    )
    return {
        "question": (
            "Is the fixed XGBoost OOS 5d long-versus-cash spread temporally "
            "consistent across the predefined OOS folds?"
        ),
        "method": {
            "oos_only": True,
            "policy": "baseline_060",
            "threshold": THRESHOLD,
            "horizon": HORIZON,
            "fold_definition": "existing 500-train / 100-test / 100-step OOS folds",
            "selection_or_tuning": False,
            "interpretation": (
                "Descriptive temporal-consistency diagnostic; fold results do not "
                "select a policy, threshold, model, or promotion decision."
            ),
        },
        "symbols": symbol_reports,
        "summary": {
            "total_symbol_folds": int(len(all_values)),
            "positive_spread_folds": int(np.sum(all_values > 0.0)),
            "negative_spread_folds": int(np.sum(all_values < 0.0)),
            "zero_spread_folds": int(np.sum(all_values == 0.0)),
            "positive_spread_fraction": float(np.mean(all_values > 0.0)),
            "all_symbol_folds_positive": bool(np.all(all_values > 0.0)),
            "mean_fold_spread": float(all_values.mean()),
            "median_fold_spread": float(np.median(all_values)),
            "min_fold_spread": float(all_values.min()),
            "max_fold_spread": float(all_values.max()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--signal-diagnostics",
        default="artifacts/xgboost-oos-signal-diagnostics/report.json",
    )
    parser.add_argument(
        "--shared-artifact-dir",
        default="artifacts/xgboost-oos-shared",
    )
    parser.add_argument(
        "--output",
        default="artifacts/xgboost-oos-temporal-spread-diagnosis/report.json",
    )
    args = parser.parse_args()

    signals = json.loads(Path(args.signal_diagnostics).read_text(encoding="utf-8"))
    artifacts = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (
            Path(args.shared_artifact_dir) / f"{symbol}.json"
            for symbol in SYMBOLS
        )
    ]
    report = evaluate(signals, artifacts)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
