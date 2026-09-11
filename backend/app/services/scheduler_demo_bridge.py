from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .order_manager import OrderIntent


@dataclass(frozen=True)
class DemoPromotionPlan:
    """A scheduler decision translated into a DEMO order intent, never submitted."""

    status: str
    symbol: str
    side: str | None = None
    quantity: float = 0.0
    reference_price: float | None = None
    signal_id: str | None = None
    reason: str | None = None
    intent: OrderIntent | None = None


class SchedulerDemoBridge:
    """Fail-closed boundary between the PAPER scheduler and DEMO execution.

    This bridge deliberately stops at an ``OrderIntent``. It never owns a
    broker, never calls ``order_send`` and never invokes the controlled DEMO
    execution service. DEMO promotion is disabled by default and requires an
    explicit symbol mapping plus an explicit enablement flag.
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        symbol_map: Mapping[str, str] | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.symbol_map = {
            str(source).strip().upper(): str(target).strip().upper()
            for source, target in (symbol_map or {}).items()
            if str(source).strip() and str(target).strip()
        }

    def plan(self, scheduler_result) -> DemoPromotionPlan:
        symbol = str(getattr(scheduler_result, "symbol", "")).strip().upper()
        signal_id = getattr(scheduler_result, "signal_id", None)
        status = str(getattr(scheduler_result, "status", "")).strip().lower()
        action = str(getattr(scheduler_result, "action", "") or "").strip().upper()
        quantity = float(getattr(scheduler_result, "quantity", 0) or 0)
        reference_price = getattr(scheduler_result, "reference_price", None)
        risk_allowed = bool(getattr(scheduler_result, "risk_allowed", False))

        if not self.enabled:
            return DemoPromotionPlan(
                status="disabled",
                symbol=symbol,
                signal_id=signal_id,
                reason="scheduler-to-DEMO promotion is disabled by default",
            )
        if status != "decided":
            return DemoPromotionPlan(
                status="blocked",
                symbol=symbol,
                signal_id=signal_id,
                reason=f"scheduler result status is not promotable: {status or 'unknown'}",
            )
        if action not in {"BUY", "SELL"}:
            return DemoPromotionPlan(
                status="blocked",
                symbol=symbol,
                signal_id=signal_id,
                reason="only BUY or SELL decisions may be promoted",
            )
        if not risk_allowed or quantity <= 0:
            return DemoPromotionPlan(
                status="blocked",
                symbol=symbol,
                signal_id=signal_id,
                reason="scheduler risk gate did not authorize a positive quantity",
            )

        demo_symbol = self.symbol_map.get(symbol)
        if not demo_symbol:
            return DemoPromotionPlan(
                status="blocked",
                symbol=symbol,
                signal_id=signal_id,
                reason="no explicit PAPER-to-DEMO symbol mapping exists",
            )

        intent = OrderIntent(
            symbol=demo_symbol,
            side=action,
            quantity=quantity,
            limit_price=float(reference_price) if reference_price is not None else None,
        )
        return DemoPromotionPlan(
            status="ready",
            symbol=demo_symbol,
            side=action,
            quantity=quantity,
            reference_price=reference_price,
            signal_id=signal_id,
            reason="DEMO intent prepared; broker submission remains disabled",
            intent=intent,
        )
