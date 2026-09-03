from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from ..firebase import FirebaseRepository
from ..settings import get_settings


class PaperDecisionLedger:
    """Bounded Firebase ledger for deterministic, resumable paper decisions."""

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

    def list_records(self, *, symbol: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        """Return a bounded set of recent ledger records, optionally by symbol."""
        if not self.firebase.enabled:
            raise RuntimeError("Firebase is required for paper ledger reads")
        if limit <= 0:
            raise ValueError("limit must be positive")
        children = self.firebase.list_children(self.path, limit=limit)
        records = [value for value in children.values() if isinstance(value, dict)]
        if symbol:
            normalized = symbol.strip().upper().removesuffix(".SA")
            records = [item for item in records if str(item.get("symbol", "")).upper() == normalized]
        records.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return records[:limit]

    def claim(
        self,
        signal_id: str,
        *,
        symbol: str,
        bar_timestamp: str,
        action: str,
        price: float | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Create a pending decision, or return the existing record.

        ``price`` is optional for backward compatibility with existing scheduler
        callers. New integrations should persist the reference price explicitly.
        """
        existing = self.get(signal_id)
        if existing is not None:
            return False, existing
        if price is not None and price <= 0:
            raise ValueError("price must be positive")

        record = {
            "signal_id": signal_id,
            "symbol": symbol.upper(),
            "bar_timestamp": bar_timestamp,
            "action": action,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "executed": False,
            "order": None,
            "outcomes": [],
        }
        if price is not None:
            record["price"] = float(price)
        self.firebase.set(self._key(signal_id), record)
        return True, record

    def complete(
        self,
        signal_id: str,
        *,
        executed: bool,
        order: dict[str, Any] | None,
        error: str | None = None,
    ) -> dict[str, Any]:
        current = self.get(signal_id)
        if current is None:
            raise KeyError(f"unknown signal_id: {signal_id}")
        current = dict(current)
        if current.get("price") is None and isinstance(order, dict):
            reference_price = order.get("reference_price")
            if reference_price is not None and float(reference_price) > 0:
                current["price"] = float(reference_price)
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

    def save_outcomes(self, signal_id: str, observations: Iterable[Any]) -> dict[str, Any]:
        """Persist completed outcome observations without losing pending horizons."""
        current = self.get(signal_id)
        if current is None:
            raise KeyError(f"unknown signal_id: {signal_id}")

        by_horizon: dict[int, dict[str, Any]] = {}
        for item in current.get("outcomes", []) or []:
            if isinstance(item, dict) and item.get("horizon_bars") is not None:
                by_horizon[int(item["horizon_bars"])] = dict(item)

        for item in observations:
            horizon = int(item.horizon_bars)
            serialized = {
                "signal_id": item.signal_id,
                "symbol": item.symbol,
                "action": item.action,
                "bar_timestamp": item.bar_timestamp,
                "decision_price": item.decision_price,
                "horizon_bars": horizon,
                "outcome_timestamp": item.outcome_timestamp,
                "outcome_price": item.outcome_price,
                "forward_return": item.forward_return,
                "signed_return": item.signed_return,
                "hit": item.hit,
            }
            previous = by_horizon.get(horizon)
            if previous is None or serialized["signed_return"] is not None:
                by_horizon[horizon] = serialized

        current = dict(current)
        current["outcomes"] = [by_horizon[key] for key in sorted(by_horizon)]
        current["outcomes_updated_at"] = datetime.now(timezone.utc).isoformat()
        self.firebase.set(self._key(signal_id), current)
        return current
