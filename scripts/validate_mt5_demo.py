from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.mt5_demo import DemoBrokerError, MetaTrader5DemoGateway, MT5DemoBroker
from app.services.operational_reconciliation import OperationalReconciler


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read and optionally reconcile a Doto/MT5 DEMO account")
    parser.add_argument("--internal-snapshot", type=Path, help="JSON internal snapshot to reconcile against MT5")
    parser.add_argument("--hours", type=int, default=24, help="Execution history window in hours (default: 24)")
    args = parser.parse_args()
    if args.hours <= 0:
        parser.error("--hours must be positive")

    server = os.environ.get("DOTO_MT5_SERVER", "").strip()
    login_raw = os.environ.get("DOTO_MT5_LOGIN", "").strip()
    password = os.environ.get("DOTO_MT5_PASSWORD")
    if not server or not login_raw or not password:
        parser.error("DOTO_MT5_SERVER, DOTO_MT5_LOGIN and DOTO_MT5_PASSWORD are required")
    if "demo" not in server.lower():
        parser.error("DOTO_MT5_SERVER must identify a DEMO server")
    try:
        login = int(login_raw)
    except ValueError as exc:
        parser.error("DOTO_MT5_LOGIN must be an integer")
        raise AssertionError from exc

    gateway = MetaTrader5DemoGateway(login=login, server=server, password=password)
    broker = MT5DemoBroker(gateway)
    date_to = _utc_now()
    date_from = date_to - timedelta(hours=args.hours)
    try:
        gateway.initialize()
        external = broker.reconciliation_snapshot(date_from, date_to)
        result: dict[str, object] = {
            "environment": broker.environment,
            "broker": broker.name,
            "account": {
                "login": broker.account().login,
                "server": broker.account().server,
                "balance": broker.account().balance,
                "equity": broker.account().equity,
                "currency": broker.account().currency,
                "trade_allowed": broker.account().trade_allowed,
            },
            "external_snapshot": external,
        }
        if args.internal_snapshot:
            internal = json.loads(args.internal_snapshot.read_text(encoding="utf-8"))
            evidence_timestamp = _parse_timestamp(str(external["captured_at"]))
            reconciliation = OperationalReconciler().evaluate(
                internal,
                external,
                evidence_timestamp=evidence_timestamp,
            )
            result["reconciliation"] = {
                "status": reconciliation.status,
                "healthy": reconciliation.healthy,
                "reasons": list(reconciliation.reasons),
                "checked_at": reconciliation.checked_at,
            }
            if not reconciliation.healthy:
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 2
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (DemoBrokerError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2
    finally:
        gateway.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
