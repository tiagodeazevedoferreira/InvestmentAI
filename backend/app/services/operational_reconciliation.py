from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isclose
from typing import Any, Mapping


@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    reasons: tuple[str, ...]
    checked_at: str

    @property
    def healthy(self) -> bool:
        return self.status == "healthy"


class OperationalReconciler:
    """Compare internal account state with an external execution snapshot.

    The evaluator is broker-neutral and read-only. It is designed to be used
    before demo/live authorization, never as an execution mechanism.
    """

    def evaluate(
        self,
        internal: Mapping[str, Any],
        external: Mapping[str, Any],
        *,
        evidence_timestamp: datetime | None = None,
        max_evidence_age_seconds: int = 120,
        cash_tolerance: float = 0.01,
    ) -> ReconciliationResult:
        reasons: list[str] = []
        if max_evidence_age_seconds <= 0:
            raise ValueError("max_evidence_age_seconds must be positive")
        if cash_tolerance < 0:
            raise ValueError("cash_tolerance must be non-negative")

        if evidence_timestamp is not None:
            ts = evidence_timestamp.astimezone(timezone.utc)
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if age < 0:
                reasons.append("reconciliation evidence timestamp is in the future")
            elif age > max_evidence_age_seconds:
                reasons.append("reconciliation evidence is stale")

        self_cash = float(internal.get("cash", 0.0))
        external_cash = float(external.get("cash", 0.0))
        if not isclose(self_cash, external_cash, abs_tol=cash_tolerance, rel_tol=0.0):
            reasons.append("cash mismatch")

        self_positions = self._positions(internal.get("positions", {}))
        external_positions = self._positions(external.get("positions", {}))
        for symbol in sorted(set(self_positions) | set(external_positions)):
            expected = self_positions.get(symbol, 0)
            observed = external_positions.get(symbol, 0)
            if expected != observed:
                reasons.append(f"position quantity mismatch: {symbol}")

        self_open = self._order_ids(internal.get("open_orders", []))
        external_open = self._order_ids(external.get("open_orders", []))
        if self_open != external_open:
            reasons.append("open order set mismatch")

        self_exec = self._execution_ids(internal.get("executions", []))
        external_exec = self._execution_ids(external.get("executions", []))
        if not self_exec.issubset(external_exec):
            reasons.append("internal executions missing externally")
        if not external_exec.issubset(self_exec):
            reasons.append("external executions missing internally")

        status = "healthy" if not reasons else "blocked"
        return ReconciliationResult(
            status=status,
            reasons=tuple(dict.fromkeys(reasons)),
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _positions(value: Any) -> dict[str, int]:
        if not isinstance(value, Mapping):
            raise ValueError("positions must be a mapping")
        result: dict[str, int] = {}
        for symbol, position in value.items():
            if isinstance(position, Mapping):
                quantity = position.get("quantity", 0)
            else:
                quantity = position
            result[str(symbol).strip().upper()] = int(quantity)
        return result

    @staticmethod
    def _order_ids(value: Any) -> set[str]:
        if not isinstance(value, list):
            raise ValueError("open_orders must be a list")
        return {str(item.get("order_id")) for item in value if isinstance(item, Mapping) and item.get("order_id")}

    @staticmethod
    def _execution_ids(value: Any) -> set[str]:
        if not isinstance(value, list):
            raise ValueError("executions must be a list")
        return {str(item.get("execution_id")) for item in value if isinstance(item, Mapping) and item.get("execution_id")}
