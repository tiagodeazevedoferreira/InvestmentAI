from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

from ..firebase import FirebaseRepository


@dataclass(frozen=True)
class FirebasePathUsage:
    path: str
    exists: bool
    records: int
    bytes: int
    status: str


@dataclass(frozen=True)
class FirebaseUsageReport:
    paths: tuple[FirebasePathUsage, ...]
    total_bytes: int
    status: str


def _json_bytes(value: Any) -> int:
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))


def _record_count(value: Any) -> int:
    return len(value) if isinstance(value, (dict, list)) else (1 if value is not None else 0)


def inspect_firebase_usage(repository: FirebaseRepository, paths: Sequence[str], *, warning_bytes: int = 500_000, critical_bytes: int = 900_000) -> FirebaseUsageReport:
    if not paths:
        raise ValueError("at least one Firebase path is required")
    if warning_bytes <= 0 or critical_bytes <= 0 or warning_bytes > critical_bytes:
        raise ValueError("usage thresholds are invalid")
    if not repository.enabled:
        raise RuntimeError("Firebase is not configured")

    results: list[FirebasePathUsage] = []
    for raw_path in paths:
        path = str(raw_path).strip().strip("/")
        if not path:
            raise ValueError("Firebase paths cannot be empty")
        value = repository.get(path)
        size = _json_bytes(value) if value is not None else 0
        status = "critical" if size >= critical_bytes else "warning" if size >= warning_bytes else "ok"
        results.append(FirebasePathUsage(path, value is not None, _record_count(value), size, status))

    total = sum(item.bytes for item in results)
    status = "critical" if any(item.status == "critical" for item in results) else "warning" if any(item.status == "warning" for item in results) else "ok"
    return FirebaseUsageReport(tuple(results), total, status)


def report_to_dict(report: FirebaseUsageReport) -> dict[str, Any]:
    return {
        "status": report.status,
        "total_bytes": report.total_bytes,
        "paths": [
            {"path": item.path, "exists": item.exists, "records": item.records, "bytes": item.bytes, "status": item.status}
            for item in report.paths
        ],
    }
