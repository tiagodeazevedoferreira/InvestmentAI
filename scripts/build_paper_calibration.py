from __future__ import annotations

import argparse
import json
import sys

from backend.app.services.market_data import download_history
from backend.app.services.paper_calibration import build_calibration_report
from backend.app.services.paper_ledger import PaperDecisionLedger
from backend.app.services.paper_outcomes import OutcomeObservation
from backend.app.services.paper_regime import classify_regime
from backend.app.services.paper_store import PaperAccountStore


def observations_from_records(records):
    observations = []
    for record in records:
        outcomes = record.get("outcomes")
        if not isinstance(outcomes, dict):
            continue
        for raw in outcomes.values():
            if not isinstance(raw, dict) or raw.get("signed_return") is None:
                continue
            observations.append(OutcomeObservation(
                str(record.get("signal_id", "")),
                str(record.get("symbol", "")).upper(),
                str(record.get("action", "")).upper(),
                str(record.get("bar_timestamp", "")),
                float(record.get("price", 0.0) or 0.0),
                int(raw.get("horizon_bars", 0)),
                raw.get("outcome_timestamp"),
                raw.get("outcome_price"),
                raw.get("forward_return"),
                raw.get("signed_return"),
                raw.get("hit"),
            ))
    return observations


def regime_by_signal(records, frame, window: int):
    labels = {}
    for record in records:
        signal_id = str(record.get("signal_id", ""))
        if not signal_id:
            continue
        result = classify_regime(frame, decision_timestamp=record.get("bar_timestamp"), window=window)
        labels[signal_id] = result.label
    return labels


def main() -> int:
    parser = argparse.ArgumentParser(description="Build descriptive calibration report from persisted paper outcomes")
    parser.add_argument("--symbols", default="PETR4,VALE3,ITUB4")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--transaction-cost-bps", type=float, default=0.0)
    parser.add_argument("--market-period", default="5y")
    parser.add_argument("--regime-window", type=int, default=20)
    parser.add_argument("--output", default="paper_calibration_report.json")
    args = parser.parse_args()
    if args.limit <= 0 or args.transaction_cost_bps < 0 or args.regime_window < 2:
        print("invalid calibration parameters", file=sys.stderr)
        return 2

    store = PaperAccountStore()
    if not store.firebase.enabled:
        print("Firebase must be configured for paper calibration", file=sys.stderr)
        return 2
    ledger = PaperDecisionLedger(firebase=store.firebase)
    observations = []
    coverage = {}
    regime_labels = {}
    for symbol in [item.strip().upper() for item in args.symbols.split(",") if item.strip()]:
        records = ledger.list_records(symbol=symbol, limit=args.limit)
        symbol_observations = observations_from_records(records)
        observations.extend(symbol_observations)
        try:
            frame = download_history(f"{symbol}.SA", period=args.market_period)
            regime_labels.update(regime_by_signal(records, frame, args.regime_window))
            regime_status = "classified"
        except (RuntimeError, ValueError) as exc:
            regime_status = f"unavailable: {exc}"
        coverage[symbol] = {
            "records": len(records),
            "completed_outcomes": len(symbol_observations),
            "regime_status": regime_status,
        }

    report = build_calibration_report(
        observations,
        transaction_cost_bps=args.transaction_cost_bps,
        regime_by_signal=regime_labels,
    )
    report["coverage"] = coverage
    report["regime"] = {
        "method": "causal_trailing_log_return_volatility_v1",
        "window": args.regime_window,
        "thresholds": {"low": 0.015, "high": 0.030},
        "lookahead_safe": True,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
