from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from backend.app.services.ci_market_data import CI_SYMBOLS, MarketDataSource, load_market_history
from backend.app.services.walk_forward import purged_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser(description="Run walk-forward analysis.")
    parser.add_argument(
        "--source",
        choices=("fixture", "provider"),
        default="fixture",
        help="Data source. The deterministic fixture is the CI default; provider is an explicit external-data mode.",
    )
    args = parser.parse_args()
    source: MarketDataSource = args.source

    results = []
    for symbol in sorted(CI_SYMBOLS):
        frame, _ = load_market_history(
            symbol,
            source=source,
            start="2021-01-04",
            end="2026-09-02",
            interval="1d",
        )
        results.append(purged_walk_forward(frame.rename(columns=str.title), symbol))

    payload = []
    for result in results:
        payload.append({
            "symbol": result.symbol,
            "folds": [asdict(fold) for fold in result.folds],
            "model": {
                "balanced_accuracy": result.model_balanced_accuracy,
                "macro_f1": result.model_macro_f1,
            },
            "baseline_ema_9_21": {
                "balanced_accuracy": result.baseline_balanced_accuracy,
                "macro_f1": result.baseline_macro_f1,
            },
            "probability_quality": {
                "raw_brier": result.raw_brier,
                "calibrated_brier": result.calibrated_brier,
                "selected_brier": result.selected_brier,
                "raw_log_loss": result.raw_log_loss,
                "calibrated_log_loss": result.calibrated_log_loss,
                "raw_ece": result.raw_ece,
                "calibrated_ece": result.calibrated_ece,
                "selected_ece": result.selected_ece,
                "selected_brier_delta_vs_raw": result.selected_brier - result.raw_brier,
                "selected_brier_delta_vs_calibrated": result.selected_brier - result.calibrated_brier,
                "selected_ece_delta_vs_raw": result.selected_ece - result.raw_ece,
                "selected_ece_delta_vs_calibrated": result.selected_ece - result.calibrated_ece,
            },
        })

    output = Path("walk_forward_report.json")
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    from scripts.summarize_walk_forward import summarize
    print("\nWALK-FORWARD STABILITY SUMMARY")
    print(json.dumps(summarize(payload), indent=2))


if __name__ == "__main__":
    main()
