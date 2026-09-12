"""Durable, broker-independent records of theoretical trading decisions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from typing import Any, Mapping

from ..firebase import FirebaseRepository
from ..settings import get_settings


class ShadowDecisionLedgerError(RuntimeError):
    """Raised when a shadow decision cannot be safely recorded or read."""


def _normalized_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper().removesuffix(".SA")
    if not normalized:
        raise ValueError("symbol is required")
    return normalized


def _normalized_timestamp(event_timestamp: str) -> str:
    value = str(event_timestamp).strip()
    if not value:
        raise ValueError("event_timestamp is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("event_timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("event_timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _normalized_name(value: str, field: str) -> str:
    normalized = str(value).strip().lower()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized


def shadow_decision_id(
    *, source: str, policy: str, symbol: str, event_timestamp: str, action: str
) -> str:
    """Return the deterministic identity for one theoretical decision event."""
    normalized_action = str(action).strip().upper()
    if normalized_action not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("action must be BUY, SELL or HOLD")
    material = "|".join(
        (
            _normalized_name(source, "source"),
            _normalized_name(policy, "policy"),
            _normalized_symbol(symbol),
            _normalized_timestamp(event_timestamp),
            normalized_action,
        )
    )
    return sha256(material.encode("utf-8")).hexdigest()[:24]


def _json_mapping(value: Mapping[str, Any] | None, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    try:
        # Firebase receives an independent, JSON-compatible snapshot rather
        # than a caller-owned object that can later be mutated in memory.
        return json.loads(json.dumps(dict(value), sort_keys=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be JSON-compatible") from exc


class ShadowDecisionLedger:
    """Bounded Firebase ledger for observational decisions without execution authority.

    The ledger has no broker, order-manager or execution dependency.  Records
    are append-only by deterministic identity: the first observation of an
    event is retained and later observations of that same event return it.
    """

    def __init__(
        self,
        firebase: FirebaseRepository | None = None,
        path: str = "paper/shadow_decision_ledger",
    ) -> None:
        if firebase is None:
            settings = get_settings()
            firebase = FirebaseRepository(
                settings.firebase_database_url,
                settings.firebase_service_account,
            )
        self.firebase = firebase
        self.path = path.strip("/")

    def _key(self, shadow_id: str) -> str:
        return f"{self.path}/{shadow_id}"

    def _require_enabled(self) -> None:
        if not self.firebase.enabled:
            raise ShadowDecisionLedgerError(
                "Firebase is required for shadow decision persistence"
            )

    def get(self, shadow_id: str) -> dict[str, Any] | None:
        normalized_id = str(shadow_id).strip()
        if not normalized_id:
            raise ValueError("shadow_id is required")
        self._require_enabled()
        try:
            value = self.firebase.get(self._key(normalized_id))
        except Exception as exc:
            raise ShadowDecisionLedgerError("shadow decision read failed") from exc
        return value if isinstance(value, dict) else None

    def list_records(
        self, *, symbol: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        self._require_enabled()
        try:
            values = self.firebase.list_children(self.path, limit=limit)
        except Exception as exc:
            raise ShadowDecisionLedgerError("shadow decision list failed") from exc
        records = [value for value in values if isinstance(value, dict)]
        if symbol:
            normalized_symbol = _normalized_symbol(symbol)
            records = [
                record
                for record in records
                if record.get("symbol") == normalized_symbol
            ]
        records.sort(key=lambda record: str(record.get("event_timestamp", "")), reverse=True)
        return records[:limit]

    def record(
        self,
        *,
        source: str,
        policy: str,
        symbol: str,
        event_timestamp: str,
        action: str,
        quantity: float | int | None = None,
        reference_price: float | None = None,
        signal: Mapping[str, Any] | None = None,
        risk: Mapping[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Persist a theoretical decision, returning ``(created, record)``.

        The identity deliberately excludes sizing and risk context: scheduler
        retries may observe a changed account state for the same completed bar.
        Keeping the first immutable observation prevents duplicate theoretical
        decisions without changing paper execution behavior.
        """
        normalized_source = _normalized_name(source, "source")
        normalized_policy = _normalized_name(policy, "policy")
        normalized_symbol = _normalized_symbol(symbol)
        normalized_timestamp = _normalized_timestamp(event_timestamp)
        normalized_action = str(action).strip().upper()
        shadow_id = shadow_decision_id(
            source=normalized_source,
            policy=normalized_policy,
            symbol=normalized_symbol,
            event_timestamp=normalized_timestamp,
            action=normalized_action,
        )
        normalized_quantity = float(quantity) if quantity is not None else None
        normalized_reference_price = (
            float(reference_price) if reference_price is not None else None
        )
        if normalized_quantity is not None and (
            not isfinite(normalized_quantity) or normalized_quantity < 0
        ):
            raise ValueError("quantity must be a finite non-negative number")
        if normalized_reference_price is not None and (
            not isfinite(normalized_reference_price) or normalized_reference_price <= 0
        ):
            raise ValueError("reference_price must be a finite positive number")

        existing = self.get(shadow_id)
        if existing is not None:
            return False, existing

        record = {
            "shadow_id": shadow_id,
            "record_type": "shadow_decision",
            "execution_authority": "none",
            "state": "recorded",
            "source": normalized_source,
            "policy": normalized_policy,
            "symbol": normalized_symbol,
            "event_timestamp": normalized_timestamp,
            "action": normalized_action,
            "quantity": normalized_quantity,
            "reference_price": normalized_reference_price,
            "signal": _json_mapping(signal, "signal"),
            "risk": _json_mapping(risk, "risk"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self.firebase.set(self._key(shadow_id), record)
        except Exception as exc:
            raise ShadowDecisionLedgerError("shadow decision persistence failed") from exc
        return True, record
