from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..firebase import FirebaseRepository
from ..settings import get_settings


class PaperDecisionLedger:
    """Bounded Firebase ledger for deterministic, resumable paper decisions."""

    def __init__(self, firebase: FirebaseRepository | None = None, path: str = "paper/decision_ledger"):
        if firebase is None:
            settings = get_settings()
            firebase = FirebaseRepository(
                settings.firebase_database_url,
                settings.firebase_service_account,
            )
        self.firebase = firebase
        self.path = path.strip("/")

    def _key(self, signal_id: str) -> str:
        return f"{self.path}/{signal_id}"

    def get(self, signal_id: str) -> dict[str, Any] | None:
        if not signal_id:
            raise ValueError("signal_id is required")
        if not self.firebase.enabled:
            raise RuntimeError("Firebase is required for paper idempotency")
        value = self.firebase.get(self._key(signal_id))
        return value if isinstance(value, dict) else None

    def claim(self, signal_id: str, *, symbol: str, bar_timestamp: str, action: str) -> tuple[bool, dict[str, Any]]:
        """Create a pending decision, or return the existing record.

        GitHub Actions concurrency prevents concurrent scheduler runs. A pending
        record is intentionally resumable if a run fails before completion.
        """
        existing = self.get(signal_id)
        if existing is not None:
            return False, existing

        record = {
            "signal_id": signal_id,
            "symbol": symbol.upper(),
            "bar_timestamp": bar_timestamp,
            "action": action,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "executed": False,
            "order": None,
        }
        self.firebase.set(self._key(signal_id), record)
        return True, record

    def complete(self, signal_id: str, *, executed: bool, order: dict[str, Any] | None, error: str | None = None) -> dict[str, Any]:
        current = self.get(signal_id)
        if current is None:
            raise KeyError(f"unknown signal_id: {signal_id}")
        current = dict(current)
        current["executed"] = bool(executed)
        current["order"] = order
        current["status"] = "completed" if error is None else "pending"
        if error is None:
            current.pop("error", None)
        else:
            current["error"] = error
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.firebase.set(self._key(signal_id), current)
        return current
