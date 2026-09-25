from datetime import datetime, timezone

import pytest

from backend.app.services.firebase_retention import FirebaseRetentionPolicy, execute_firebase_cleanup, plan_firebase_cleanup


class FakeFirebase:
    enabled = True
    def __init__(self, records):
        self.records = records
        self.deleted = []
    def list_children(self, path, *, limit=200):
        return self.records.get(path, [])[:limit]
    def delete(self, path):
        self.deleted.append(path)


NOW = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)


def test_plan_selects_only_old_records():
    repo = FakeFirebase({"paper/decision_ledger": [
        {"signal_id": "old", "created_at": "2026-09-01T12:00:00+00:00"},
        {"signal_id": "new", "created_at": "2026-09-20T12:00:00+00:00"},
    ]})
    report = plan_firebase_cleanup(repo, [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW)
    assert report.dry_run and report.eligible == 1
    assert report.candidates[0].key == "old"
    assert repo.deleted == []


def test_invalid_timestamp_is_never_deleted():
    repo = FakeFirebase({"paper/decision_ledger": [{"signal_id": "unknown", "created_at": "not-a-date"}]})
    report = plan_firebase_cleanup(repo, [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW)
    assert report.eligible == 0 and report.skipped_invalid_timestamps == 1
    assert repo.deleted == []


def test_dry_run_never_deletes():
    repo = FakeFirebase({"paper/decision_ledger": [{"signal_id": "old", "created_at": "2026-09-01T12:00:00+00:00"}]})
    report = plan_firebase_cleanup(repo, [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW)
    result = execute_firebase_cleanup(repo, report, dry_run=True)
    assert result.deleted == 0 and repo.deleted == []


def test_deletion_requires_explicit_non_dry_run():
    repo = FakeFirebase({"paper/decision_ledger": [{"signal_id": "old", "created_at": "2026-09-01T12:00:00+00:00"}]})
    report = plan_firebase_cleanup(repo, [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW)
    result = execute_firebase_cleanup(repo, report, dry_run=False)
    assert result.deleted == 1
    assert repo.deleted == ["paper/decision_ledger/old"]


def test_max_deletions_caps_cleanup():
    repo = FakeFirebase({"paper/decision_ledger": [
        {"signal_id": "old-1", "created_at": "2026-08-01T12:00:00+00:00"},
        {"signal_id": "old-2", "created_at": "2026-08-02T12:00:00+00:00"},
    ]})
    report = plan_firebase_cleanup(repo, [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW, max_deletions=1)
    assert report.eligible == 1


def test_validation():
    with pytest.raises(ValueError): FirebaseRetentionPolicy("", 7)
    with pytest.raises(ValueError): FirebaseRetentionPolicy("paper/decision_ledger", 0)
    with pytest.raises(ValueError): plan_firebase_cleanup(FakeFirebase({}), [], now=NOW)
    with pytest.raises(ValueError): plan_firebase_cleanup(FakeFirebase({}), [FirebaseRetentionPolicy("paper/decision_ledger", 7)], now=NOW, max_deletions=0)
