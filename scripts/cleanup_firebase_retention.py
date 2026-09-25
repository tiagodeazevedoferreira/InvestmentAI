from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.firebase import FirebaseRepository
from backend.app.services.firebase_retention import (
    FirebaseRetentionPolicy,
    execute_firebase_cleanup,
    plan_firebase_cleanup,
    report_to_dict,
)

DEFAULT_POLICIES = (
    ("paper/decision_ledger", 180),
    ("paper/shadow_decision_ledger", 180),
)


def main() -> int:
    service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    database_url = os.environ.get("FIREBASE_DATABASE_URL")
    max_deletions = int(os.environ.get("FIREBASE_RETENTION_MAX_DELETIONS") or "100")
    dry_run = (os.environ.get("FIREBASE_RETENTION_DRY_RUN") or "true").strip().lower() in {"1", "true", "yes", "on"}

    policies = []
    for raw in (os.environ.get("FIREBASE_RETENTION_POLICIES") or "").split(","):
        item = raw.strip()
        if not item:
            continue
        path, days = item.split(":", 1)
        policies.append(FirebaseRetentionPolicy(path, int(days)))
    if not policies:
        policies = [FirebaseRetentionPolicy(path, days) for path, days in DEFAULT_POLICIES]

    repository = FirebaseRepository(database_url, service_account)
    report = plan_firebase_cleanup(repository, policies, max_deletions=max_deletions)
    if not dry_run:
        report = execute_firebase_cleanup(repository, report, dry_run=False)

    payload = report_to_dict(report)
    output = Path(os.environ.get("FIREBASE_RETENTION_OUTPUT", "firebase-retention-report.json"))
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Firebase retention dry-run: {report.dry_run}")
    print(f"Scanned: {report.scanned}; eligible: {report.eligible}; deleted: {report.deleted}")
    print(f"Skipped invalid timestamps/keys: {report.skipped_invalid_timestamps}")
    for candidate in report.candidates:
        print(f"- {candidate.path}/{candidate.key}: {candidate.age_days:.1f} days old")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
