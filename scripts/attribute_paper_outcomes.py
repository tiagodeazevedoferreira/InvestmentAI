from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

from backend.app.services.paper_ledger import PaperDecisionLedger
from backend.app.services.paper_outcomes import attribute_decision
from backend.app.services.paper_scheduler import DEFAULT_SYMBOLS, yahoo_symbol
from backend.app.services.paper_store import PaperAccountStore
from backend.app.services.providers import get_provider


DEFAULT_LIMIT = 200


def decision_price(frame: pd.DataFrame, timestamp: str) -> float:
    target = pd.Timestamp(timestamp)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    else:
        target = target.tz_convert("UTC")

    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    matches = index == target
    if not matches.any():
        raise ValueError(f"decision timestamp not found in market data: {timestamp}")
    return float(pd.to_numeric(frame.loc[matches, "Close"].iloc[0]))


def attribute_symbol(ledger: PaperDecisionLedger, provider, symbol: str, *, period: str, limit: int) -> dict:
    display_symbol = symbol.strip().upper().removesuffix(".SA")
    frame = provider.history(yahoo_symbol(display_symbol), period=period)
    if frame.empty:
        raise ValueError(f"No market data for {display_symbol}")
    if not frame.index.is_monotonic_increasing:
        frame = frame.sort_index()

    records = ledger.list_records(symbol=display_symbol, limit=limit)
    persisted = 0
    incomplete = 0
    skipped = 0
    for record in records:
        if record.get("status") != "completed":
            skipped += 1
            continue
        try:
            price = float(record.get("price") or decision_price(frame, str(record["bar_timestamp"])))
            decision = dict(record)
            decision["price"] = price
            observations = attribute_decision(decision, frame)
        except (KeyError, TypeError, ValueError):
            skipped += 1
            continue

        if any(item.signed_return is not None for item in observations):
            ledger.save_outcomes(record["signal_id"], observations)
            persisted += 1
        if any(item.signed_return is None for item in observations):
            incomplete += 1

    return {
        "symbol": display_symbol,
        "records": len(records),
        "persisted": persisted,
        "incomplete_horizons": incomplete,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist forward outcomes for completed InvestmentAI paper decisions")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--period", default="3mo")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    if args.limit <= 0:
        print("--limit must be positive", file=sys.stderr)
        return 2

    store = PaperAccountStore()
    if not store.firebase.enabled:
        print("Firebase must be configured for paper outcome persistence", file=sys.stderr)
        return 2

    ledger = PaperDecisionLedger(firebase=store.firebase)
    provider = get_provider("openbb")
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    results = []
    for symbol in symbols:
        try:
            results.append(attribute_symbol(ledger, provider, symbol, period=args.period, limit=args.limit))
        except Exception as exc:
            results.append({"symbol": symbol, "status": "error", "reason": str(exc)})

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if any(item.get("status") == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
