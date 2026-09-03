from __future__ import annotations

import argparse
import json
import os
import sys

from backend.app.services.paper_scheduler import DEFAULT_SYMBOLS, run_scheduler


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the broker-independent InvestmentAI paper scheduler")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS), help="Comma-separated B3 symbols")
    parser.add_argument("--period", default="3mo")
    parser.add_argument("--target-allocation", type=float, default=0.05)
    parser.add_argument("--shadow", action="store_true", help="Record decisions without mutating the paper account")
    parser.add_argument("--force", action="store_true", help="Bypass the B3 session-time guard; intended for manual validation")
    args = parser.parse_args()

    enabled = os.getenv("PAPER_AUTOMATION_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        print(json.dumps({"status": "disabled", "reason": "PAPER_AUTOMATION_ENABLED is not true"}))
        return 0

    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    if not symbols:
        print("No symbols configured", file=sys.stderr)
        return 2

    results = run_scheduler(
        symbols,
        period=args.period,
        target_allocation=args.target_allocation,
        execute=not args.shadow,
        force=args.force,
    )
    payload = [result.__dict__ for result in results]
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 1 if any(item["status"] == "error" for item in payload) else 0


if __name__ == "__main__":
    raise SystemExit(main())
