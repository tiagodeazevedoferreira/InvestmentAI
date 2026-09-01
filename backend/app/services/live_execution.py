from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .live_authorization import LiveAuthorizationGate
from .order_manager import OrderIntent


class LiveBroker(Protocol):
    environment: str

    def submit(self, intent: OrderIntent) -> dict: ...

    def cancel(self, order_id: str) -> dict: ...

    def positions(self) -> list[dict]: ...


@dataclass
class LiveExecutionService:
    broker: LiveBroker
    authorization: LiveAuthorizationGate

    def submit(
        self,
        intent: OrderIntent,
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
        signal_confidence: float,
    ) -> dict:
        auth = self.authorization.evaluate(
            trading_mode=trading_mode,
            live_trading_enabled=live_trading_enabled,
            model_approved=model_approved,
            risk_gate_enabled=risk_gate_enabled,
            shadow_validation_passed=shadow_validation_passed,
            kill_switch=kill_switch,
            reconciliation_healthy=reconciliation_healthy,
            broker_demo_validated=broker_demo_validated,
            max_position_notional=max_position_notional,
            proposed_notional=(intent.quantity * intent.limit_price) if intent.limit_price else 0,
            signal_confidence=signal_confidence,
        )
        if not auth.authorized:
            raise PermissionError("Live execution blocked: " + "; ".join(auth.reasons))
        if getattr(self.broker, "environment", "") != "live":
            raise PermissionError("Live broker environment mismatch")
        return self.broker.submit(intent)
