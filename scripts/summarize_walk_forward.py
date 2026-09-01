"""Summarize walk-forward fold results for ML vs EMA baseline.

Reads a JSON report produced by the walk-forward runner and reports aggregate
and per-symbol stability statistics. No model fitting or trading decisions are
performed here.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev


def summarize(records: list[dict]) -> dict:
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_symbol[record["symbol"]].append(record)

    output = {}
    for symbol, items in sorted(by_symbol.items()):
        folds = [fold for item in items for fold in item.get("folds", [])]
        wins_ba = sum(f["model_balanced_accuracy"] > f["baseline_balanced_accuracy"] for f in folds)
        wins_f1 = sum(f["model_macro_f1"] > f["baseline_macro_f1"] for f in folds)
        ba_delta = [f["model_balanced_accuracy"] - f["baseline_balanced_accuracy"] for f in folds]
        f1_delta = [f["model_macro_f1"] - f["baseline_macro_f1"] for f in folds]
        output[symbol] = {
            "folds": len(folds),
            "model_balanced_accuracy_mean": mean(f["model_balanced_accuracy"] for f in folds),
            "model_balanced_accuracy_median": median(f["model_balanced_accuracy"] for f in folds),
            "model_balanced_accuracy_std": pstdev(f["model_balanced_accuracy"] for f in folds),
            "baseline_balanced_accuracy_mean": mean(f["baseline_balanced_accuracy"] for f in folds),
            "model_macro_f1_mean": mean(f["model_macro_f1"] for f in folds),
            "baseline_macro_f1_mean": mean(f["baseline_macro_f1"] for f in folds),
            "mean_balanced_accuracy_delta": mean(ba_delta),
            "median_balanced_accuracy_delta": median(ba_delta),
            "mean_macro_f1_delta": mean(f1_delta),
            "median_macro_f1_delta": median(f1_delta),
            "folds_model_wins_balanced_accuracy": wins_ba,
            "folds_model_wins_macro_f1": wins_f1,
            "fold_win_rate_balanced_accuracy": wins_ba / len(folds),
            "fold_win_rate_macro_f1": wins_f1 / len(folds),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    data = json.loads(args.report.read_text())
    print(json.dumps(summarize(data), indent=2))


if __name__ == "__main__":
    main()
