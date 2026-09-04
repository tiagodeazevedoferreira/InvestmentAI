from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from .operational_kill_switch import OperationalKillSwitch
from .operational_reconciliation import OperationalReconciler, ReconciliationResult


class DemoAuthorizationBlocked(PermissionError):
    """Raised when demo execution is not operationally authorized."""


@dataclass(frozen=True)
class DemoAuthorizationResult:
    allowed: bool
    reasons: tuple[str, ...]
    reconciliation: ReconciliationResult | None


class DemoAuthorizationGate:
    """Fail-closed authorization boundary for the DEMO execution environment.

    This class does not submit orders. It only decides whether a caller may
    proceed to a DEMO broker after independent operational checks pass.
    """

    def __init__(
        self,
        kill_switch: OperationalKillSwitch,
        reconciler: OperationalReconciler | None = None,
        *,
        max_evidence_age_seconds: int = 120,
        cash_tolerance: float = 0.01,
    ) -> None:
        if max_evidence_age_seconds <= 0:
            raise ValueError("max_evidence_age_seconds must be positive")
        if cash_tolerance < 0:
            raise ValueError("cash_tolerance must be non-negative")
        self.kill_switch = kill_switch
        self.reconciler = reconciler or OperationalReconciler()
        self.max_evidence_age_seconds = max_evidence_age_seconds
        self.cash_tolerance = cash_tolerance

    def authorize(
        self,
        *,
        environment: str,
        internal: Mapping[str, Any],
        external: Mapping[str, Any],
        evidence_timestamp: datetime | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> DemoAuthorizationResult:
        reasons: list[str] = []
        if environment.strip().lower() != "demo":
            reasons.append("demo authorization requires environment=demo")

        if not self.kill_switch.allows_operation():
            reasons.append("kill switch is active")

        reconciliation = None
        if not reasons:
            reconciliation = self.reconciler.evaluate(
                internal,
                external,
                evidence_timestamp=evidence_timestamp,
                max_evidence_age_seconds=self.max_evidence_age_seconds,
                cash_tolerance=self.cash_tolerance,
                now=now,
            )
            if not reconciliation.healthy:
                reasons.extend(reconciliation.reasons)

        return DemoAuthorizationResult(
            allowed=not reasons,
            reasons=tuple(dict.fromkeys(reasons)),
            reconciliation=reconciliation,
        )

    def require_authorized(
        self,
        *,
        environment: str,
        internal: Mapping[str, Any],
        external: Mapping[str, Any],
        evidence_timestamp: datetime | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> DemoAuthorizationResult:
        result = self.authorize(
            environment=environment,
            internal=internal,
            external=external,
            evidence_timestamp=evidence_timestamp,
            now=now,
        )
        if not result.allowed:
            detail = "; ".join(result.reasons) or "authorization failed"
            raise DemoAuthorizationBlocked(detail)
        return result
