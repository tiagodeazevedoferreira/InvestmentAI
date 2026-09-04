from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol

from .demo_authorization import DemoAuthorizationGate, DemoAuthorizationResult
from .order_manager import OrderIntent
from .operational_reconciliation import OperationalReconciler, ReconciliationResult


class DemoExecutionBroker(Protocol):
    environment: str

    def reconciliation_snapshot(self, date_from: datetime, date_to: datetime) -> Mapping[str, Any]: ...

    def submit(self, intent: OrderIntent) -> Mapping[str, Any]: ...


class DemoExecutionBlocked(PermissionError):
    """Raised when an authorized DEMO execution cannot be completed safely."""


@dataclass(frozen=True)
class DemoExecutionResult:
    execution: Mapping[str, Any]
    authorization: DemoAuthorizationResult
    post_reconciliation: ReconciliationResult


class AuthorizedDemoExecutor:
    """Execute one DEMO order behind pre/post operational reconciliation.

    The executor is deliberately not connected to the scheduler. A caller
    must provide the internal state before execution and a fresh internal
    state after the broker operation. The broker is therefore never treated
    as the source of truth for the application's internal ledger.
    """

    def __init__(
        self,
        broker: DemoExecutionBroker,
        gate: DemoAuthorizationGate,
        *,
        reconciliation_window_seconds: int = 300,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if reconciliation_window_seconds <= 0:
            raise ValueError("reconciliation_window_seconds must be positive")
        self.broker = broker
        self.gate = gate
        self.reconciliation_window_seconds = reconciliation_window_seconds
        self._now = now or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        intent: OrderIntent,
        *,
        internal_before: Mapping[str, Any],
        internal_after: Mapping[str, Any],
    ) -> DemoExecutionResult:
        if str(getattr(self.broker, "environment", "")).strip().lower() != "demo":
            raise DemoExecutionBlocked("DEMO executor requires a broker with environment=demo")

        before = self._now().astimezone(timezone.utc)
        external_before = self.broker.reconciliation_snapshot(
            before - __import__("datetime").timedelta(seconds=self.reconciliation_window_seconds),
            before,
        )
        evidence_timestamp = self._snapshot_timestamp(external_before)
        authorization = self.gate.require_authorized(
            environment="demo",
            internal=internal_before,
            external=external_before,
            evidence_timestamp=evidence_timestamp,
        )

        execution = self.broker.submit(intent)

        after = self._now().astimezone(timezone.utc)
        external_after = self.broker.reconciliation_snapshot(
            after - __import__("datetime").timedelta(seconds=self.reconciliation_window_seconds),
            after,
        )
        post_evidence_timestamp = self._snapshot_timestamp(external_after)
        post_reconciliation = self.gate.reconciler.evaluate(
            internal_after,
            external_after,
            evidence_timestamp=post_evidence_timestamp,
            max_evidence_age_seconds=self.gate.max_evidence_age_seconds,
            cash_tolerance=self.gate.cash_tolerance,
        )
        if not post_reconciliation.healthy:
            raise DemoExecutionBlocked(
                "post-execution reconciliation failed: "
                + "; ".join(post_reconciliation.reasons)
            )

        return DemoExecutionResult(
            execution=execution,
            authorization=authorization,
            post_reconciliation=post_reconciliation,
        )

    @staticmethod
    def _snapshot_timestamp(snapshot: Mapping[str, Any]) -> datetime | None:
        value = snapshot.get("captured_at")
        if not value:
            return None
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        raise ValueError("external snapshot captured_at must be an ISO timestamp")
