from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from backend.app.services.openbb_market_data import B3_SYMBOLS, OpenBBMarketDataProvider
from backend.app.services.walk_forward import purged_walk_forward


def main() -> None:
    provider = OpenBBMarketDataProvider()
    results = []
    for symbol in sorted(B3_SYMBOLS):
        frame = provider.historical(symbol, start="2021-01-04", end="2026-09-02", interval="1d")
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
                "raw_log_loss": result.raw_log_loss,
                "calibrated_log_loss": result.calibrated_log_loss,
                "raw_ece": result.raw_ece,
                "calibrated_ece": result.calibrated_ece,
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
