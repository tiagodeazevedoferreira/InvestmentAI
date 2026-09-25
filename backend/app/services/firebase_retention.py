from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from ..firebase import FirebaseRepository


@dataclass(frozen=True)
class FirebaseRetentionPolicy:
    path: str
    retention_days: int
    timestamp_field: str = "created_at"

    def __post_init__(self) -> None:
        if not self.path.strip("/"):
            raise ValueError("path is required")
        if self.retention_days <= 0:
            raise ValueError("retention_days must be positive")
        if not self.timestamp_field.strip():
            raise ValueError("timestamp_field is required")


@dataclass(frozen=True)
class FirebaseCleanupCandidate:
    path: str
    key: str
    timestamp: str
    age_days: float


@dataclass(frozen=True)
class FirebaseCleanupReport:
    dry_run: bool
    scanned: int
    eligible: int
    deleted: int
    skipped_invalid_timestamps: int
    candidates: tuple[FirebaseCleanupCandidate, ...]


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def _record_key(record: dict[str, Any]) -> str:
    for field in ("signal_id", "shadow_id"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("record has no supported immutable key")


def plan_firebase_cleanup(repository: FirebaseRepository, policies: Sequence[FirebaseRetentionPolicy], *, now: datetime | None = None, max_deletions: int = 100) -> FirebaseCleanupReport:
    if not repository.enabled:
        raise RuntimeError("Firebase is not configured")
    if not policies:
        raise ValueError("at least one retention policy is required")
    if max_deletions <= 0:
        raise ValueError("max_deletions must be positive")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    candidates: list[FirebaseCleanupCandidate] = []
    scanned = 0
    skipped = 0
    for policy in policies:
        path = policy.path.strip("/")
        cutoff = current - timedelta(days=policy.retention_days)
        for record in repository.list_children(path, limit=max_deletions):
            scanned += 1
            if not isinstance(record, dict):
                skipped += 1
                continue
            timestamp = _parse_timestamp(record.get(policy.timestamp_field))
            if timestamp is None:
                skipped += 1
                continue
            if timestamp >= cutoff:
                continue
            try:
                key = _record_key(record)
            except ValueError:
                skipped += 1
                continue
            candidates.append(FirebaseCleanupCandidate(path, key, timestamp.isoformat(), (current - timestamp).total_seconds() / 86400.0))
            if len(candidates) >= max_deletions:
                break
        if len(candidates) >= max_deletions:
            break
    return FirebaseCleanupReport(True, scanned, len(candidates), 0, skipped, tuple(candidates))


def execute_firebase_cleanup(repository: FirebaseRepository, report: FirebaseCleanupReport, *, dry_run: bool = True) -> FirebaseCleanupReport:
    if not report.dry_run:
        raise ValueError("cleanup report must originate from a dry-run plan")
    if dry_run:
        return report
    for candidate in report.candidates:
        repository.delete(f"{candidate.path}/{candidate.key}")
    return FirebaseCleanupReport(False, report.scanned, report.eligible, len(report.candidates), report.skipped_invalid_timestamps, report.candidates)


def report_to_dict(report: FirebaseCleanupReport) -> dict[str, Any]:
    return {"dry_run": report.dry_run, "scanned": report.scanned, "eligible": report.eligible, "deleted": report.deleted, "skipped_invalid_timestamps": report.skipped_invalid_timestamps, "candidates": [{"path": c.path, "key": c.key, "timestamp": c.timestamp, "age_days": round(c.age_days, 3)} for c in report.candidates]}
