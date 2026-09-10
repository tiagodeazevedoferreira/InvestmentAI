from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Protocol

from .demo_authorization import DemoAuthorizationGate, DemoAuthorizationResult
from .demo_order_preflight import DemoOrderPreflight
from .order_manager import OrderIntent
from .operational_reconciliation import ReconciliationResult


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
    """Execute one DEMO order behind deterministic preflight and reconciliation.

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
        preflight: DemoOrderPreflight | None = None,
    ) -> None:
        if reconciliation_window_seconds <= 0:
            raise ValueError("reconciliation_window_seconds must be positive")
        self.broker = broker
        self.gate = gate
        self.reconciliation_window_seconds = reconciliation_window_seconds
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.preflight = preflight or DemoOrderPreflight()

    def execute(
        self,
        intent: OrderIntent,
        *,
        internal_before: Mapping[str, Any],
        internal_after: Mapping[str, Any],
        on_authorized: Callable[[], None] | None = None,
        on_submitted: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> DemoExecutionResult:
        if str(getattr(self.broker, "environment", "")).strip().lower() != "demo":
            raise DemoExecutionBlocked("DEMO executor requires a broker with environment=demo")

        try:
            normalized_intent = self.preflight.validate(intent, environment="demo")
            self.preflight.validate_state(internal_before)
            self.preflight.validate_state(internal_after)
        except (ValueError, TypeError) as exc:
            raise DemoExecutionBlocked(f"DEMO order preflight failed: {exc}") from exc

        before = self._now().astimezone(timezone.utc)
        external_before = self.broker.reconciliation_snapshot(
            before - timedelta(seconds=self.reconciliation_window_seconds),
            before,
        )
        evidence_timestamp = self._snapshot_timestamp(external_before)
        authorization = self.gate.require_authorized(
            environment="demo",
            internal=internal_before,
            external=external_before,
            evidence_timestamp=evidence_timestamp,
            now=lambda: before,
        )
        if on_authorized is not None:
            on_authorized()

        execution = self.broker.submit(normalized_intent)
        if on_submitted is not None:
            on_submitted(execution)

        after = self._now().astimezone(timezone.utc)
        external_after = self.broker.reconciliation_snapshot(
            after - timedelta(seconds=self.reconciliation_window_seconds),
            after,
        )
        post_evidence_timestamp = self._snapshot_timestamp(external_after)
        post_reconciliation = self.gate.reconciler.evaluate(
            internal_after,
            external_after,
            evidence_timestamp=post_evidence_timestamp,
            max_evidence_age_seconds=self.gate.max_evidence_age_seconds,
            cash_tolerance=self.gate.cash_tolerance,
            now=lambda: after,
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
