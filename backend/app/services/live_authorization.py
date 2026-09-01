from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class LiveAuthorization:
    authorized: bool
    reasons: tuple[str, ...]


class LiveAuthorizationGate:
    """Final fail-closed gate for real-money execution.

    This class deliberately requires explicit configuration for every live
    safety control. Provider signals never authorize live trading directly.
    """

    def evaluate(
        self,
        *,
        trading_mode: str,
        live_trading_enabled: bool,
        model_approved: bool,
        risk_gate_enabled: bool,
        shadow_validation_passed: bool,
        kill_switch: bool,
        reconciliation_healthy: bool,
        broker_demo_validated: bool,
        max_position_notional: float,
        proposed_notional: float,
        signal_confidence: float,
        min_live_confidence: float = 0.75,
        timestamp: datetime | None = None,
    ) -> LiveAuthorization:
        reasons: list[str] = []
        if trading_mode.lower() != "live":
            reasons.append("trading mode is not live")
        if not live_trading_enabled:
            reasons.append("live trading is disabled")
        if not model_approved:
            reasons.append("model is not approved")
        if not risk_gate_enabled:
            reasons.append("risk gate is disabled")
        if not shadow_validation_passed:
            reasons.append("shadow validation has not passed")
        if kill_switch:
            reasons.append("kill switch is active")
        if not reconciliation_healthy:
            reasons.append("broker reconciliation is unhealthy")
        if not broker_demo_validated:
            reasons.append("broker demo validation has not passed")
        if max_position_notional <= 0:
            reasons.append("max position notional is not configured")
        if proposed_notional <= 0:
            reasons.append("proposed notional must be positive")
        if proposed_notional > max_position_notional:
            reasons.append("proposed notional exceeds live limit")
        if signal_confidence < min_live_confidence:
            reasons.append("live confidence threshold not met")
        if timestamp is not None:
            age = (datetime.now(timezone.utc) - timestamp).total_seconds()
            if age > 300:
                reasons.append("live authorization signal is stale")

        return LiveAuthorization(not reasons, tuple(dict.fromkeys(reasons)))
