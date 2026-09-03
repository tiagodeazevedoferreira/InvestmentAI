from __future__ import annotations

import argparse
import json
import sys

from backend.app.services.paper_calibration import build_calibration_report
from backend.app.services.paper_ledger import PaperDecisionLedger
from backend.app.services.paper_outcomes import OutcomeObservation
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build descriptive calibration report from persisted paper outcomes")
    parser.add_argument("--symbols", default="PETR4,VALE3,ITUB4")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--transaction-cost-bps", type=float, default=0.0)
    parser.add_argument("--output", default="paper_calibration_report.json")
    args = parser.parse_args()
    if args.limit <= 0 or args.transaction_cost_bps < 0:
        print("limit must be positive and transaction cost must be non-negative", file=sys.stderr)
        return 2

    store = PaperAccountStore()
    if not store.firebase.enabled:
        print("Firebase must be configured for paper calibration", file=sys.stderr)
        return 2
    ledger = PaperDecisionLedger(firebase=store.firebase)
    observations = []
    coverage = {}
    for symbol in [item.strip().upper() for item in args.symbols.split(",") if item.strip()]:
        records = ledger.list_records(symbol=symbol, limit=args.limit)
        symbol_observations = observations_from_records(records)
        observations.extend(symbol_observations)
        coverage[symbol] = {"records": len(records), "completed_outcomes": len(symbol_observations)}

    report = build_calibration_report(observations, transaction_cost_bps=args.transaction_cost_bps)
    report["coverage"] = coverage
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
