from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..firebase import FirebaseRepository
from ..settings import get_settings


class PaperDecisionLedger:
    """Bounded Firebase ledger for deterministic paper decisions.

    The signal id is derived from symbol + confirmed bar timestamp + action, so
    re-running a scheduler for the same bar cannot create a second paper order.
    """

    def __init__(self, firebase: FirebaseRepository | None = None, path: str = "paper/decision_ledger"):
        settings = get_settings()
        self.firebase = firebase or FirebaseRepository(
            settings.firebase_database_url,
            settings.firebase_service_account,
        )
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
        """Record a decision if unseen; return (created, record).

        Firebase RTDB does not expose a compare-and-set primitive through our
        abstraction. The scheduler is therefore additionally serialized by the
        GitHub Actions concurrency group. The persisted key is still the source
        of truth for retries and duplicate invocations.
        """
        existing = self.get(signal_id)
        if existing is not None:
            return False, existing

        record = {
            "signal_id": signal_id,
            "symbol": symbol.upper(),
            "bar_timestamp": bar_timestamp,
            "action": action,
            "status": "decided",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "executed": False,
            "order": None,
        }
        self.firebase.set(self._key(signal_id), record)
        return True, record

    def mark_executed(self, signal_id: str, order: dict[str, Any] | None) -> dict[str, Any]:
        current = self.get(signal_id)
        if current is None:
            raise KeyError(f"unknown signal_id: {signal_id}")
        current = dict(current)
        current["executed"] = order is not None
        current["order"] = order
        current["status"] = "executed" if order is not None else "decided"
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.firebase.set(self._key(signal_id), current)
        return current
