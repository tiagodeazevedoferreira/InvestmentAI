from __future__ import annotations

import json
from pathlib import Path

from backend.app.services.probability_evaluation import paired_fold_summary

REPORT = Path("walk_forward_report.json")
OUTPUT = Path("probability_selection_statistics.json")


def _symbol_results(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        symbols = payload.get("results", payload)
        if isinstance(symbols, dict):
            return [
                {"symbol": symbol, **result}
                for symbol, result in symbols.items()
                if isinstance(result, dict)
            ]
    raise ValueError("walk-forward report must contain a list of symbol results or a symbol-keyed results object")


def main() -> None:
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    results = _symbol_results(payload)

    output: dict[str, list[dict[str, object]]] = {}
    for result in results:
        symbol = str(result.get("symbol", ""))
        folds = result.get("folds", [])
        if not symbol or not isinstance(folds, list) or len(folds) < 2:
            continue

        raw_brier = [float(f["raw_brier"]) for f in folds]
        calibrated_brier = [float(f["calibrated_brier"]) for f in folds]
        raw_ece = [float(f["raw_ece"]) for f in folds]
        calibrated_ece = [float(f["calibrated_ece"]) for f in folds]

        # Selected metrics are stored per regime. Reconstruct each fold's
        # selected metric as the row-weighted combination of its regimes.
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
