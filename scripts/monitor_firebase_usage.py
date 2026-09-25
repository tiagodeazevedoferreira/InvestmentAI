from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.firebase import FirebaseRepository
from backend.app.services.firebase_governance import inspect_firebase_usage, report_to_dict

DEFAULT_PATHS = ("paper/account", "paper/decision_ledger", "paper/shadow_decision_ledger", "system/diagnostics/github_actions")


def main() -> int:
    service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    database_url = os.environ.get("FIREBASE_DATABASE_URL")
    paths = tuple(item.strip().strip("/") for item in (os.environ.get("FIREBASE_MONITOR_PATHS") or ",".join(DEFAULT_PATHS)).split(",") if item.strip())
    warning = int(os.environ.get("FIREBASE_USAGE_WARNING_BYTES") or "500000")
    critical = int(os.environ.get("FIREBASE_USAGE_CRITICAL_BYTES") or "900000")
    repository = FirebaseRepository(database_url, service_account)
    report = inspect_firebase_usage(repository, paths, warning_bytes=warning, critical_bytes=critical)
    payload = report_to_dict(report)
    output = Path(os.environ.get("FIREBASE_USAGE_OUTPUT", "firebase-usage-report.json"))
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Firebase usage status: {report.status}")
    print(f"Total monitored bytes: {report.total_bytes}")
    for item in report.paths:
        print(f"- {item.path}: {item.bytes} bytes, {item.records} records, {item.status}")
    return 2 if report.status == "critical" else 0


if __name__ == "__main__":
    raise SystemExit(main())
