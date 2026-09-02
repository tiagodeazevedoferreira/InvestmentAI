from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.probability_evaluation import paired_fold_summary

REPORT = Path("walk_forward_report.json")
OUTPUT = Path("probability_selection_statistics.json")


def main() -> None:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    symbols = payload.get("results", payload)
    if not isinstance(symbols, dict):
        raise ValueError("walk-forward report must contain a symbol-keyed results object")

    output: dict[str, list[dict[str, object]]] = {}
    for symbol, result in symbols.items():
        folds = result.get("folds", [])
        if len(folds) < 2:
            continue

        raw_brier = [float(f["raw_brier"]) for f in folds]
        calibrated_brier = [float(f["calibrated_brier"]) for f in folds]
        raw_ece = [float(f["raw_ece"]) for f in folds]
        calibrated_ece = [float(f["calibrated_ece"]) for f in folds]

        # Selected metrics are evaluated at regime level. To keep the paired
        # comparison at fold granularity, reconstruct each fold's selected
        # metric as the row-weighted combination of its regime metrics.
        selected_brier: list[float] = []
        selected_ece: list[float] = []
        for fold in folds:
            regimes = fold.get("regime_metrics", [])
            rows = sum(int(m["test_rows"]) for m in regimes)
            if not regimes or rows == 0:
                raise ValueError(f"missing regime metrics for {symbol} fold {fold.get('fold')}")
            selected_brier.append(sum(float(m["selected_brier"]) * int(m["test_rows"]) for m in regimes) / rows)
            selected_ece.append(sum(float(m["selected_ece"]) * int(m["test_rows"]) for m in regimes) / rows)

        output[symbol] = [
            paired_fold_summary(raw_brier, calibrated_brier, metric="brier", comparison="calibrated_vs_raw").__dict__,
            paired_fold_summary(raw_brier, selected_brier, metric="brier", comparison="selected_vs_raw").__dict__,
            paired_fold_summary(calibrated_brier, selected_brier, metric="brier", comparison="selected_vs_calibrated").__dict__,
            paired_fold_summary(raw_ece, calibrated_ece, metric="ece", comparison="calibrated_vs_raw").__dict__,
            paired_fold_summary(raw_ece, selected_ece, metric="ece", comparison="selected_vs_raw").__dict__,
            paired_fold_summary(calibrated_ece, selected_ece, metric="ece", comparison="selected_vs_calibrated").__dict__,
        ]

    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
