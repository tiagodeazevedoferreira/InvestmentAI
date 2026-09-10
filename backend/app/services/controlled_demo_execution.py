from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from uuid import uuid4

from .demo_execution import AuthorizedDemoExecutor, DemoExecutionResult
from .demo_ledger import DemoOrderLedger, DemoOrderRecord
from .order_manager import OrderIntent


@dataclass(frozen=True)
class ControlledDemoExecutionResult:
    record: DemoOrderRecord
    execution: DemoExecutionResult


class ControlledDemoExecutionService:
    """Orchestrate one explicitly requested DEMO order with durable lifecycle state.

    This service is intentionally manual-call only. It has no scheduler hook,
    no signal generation, and no automatic retry. A submitted order is never
    retried automatically because a process crash can occur after broker
    acceptance and before local persistence.
    """

    def __init__(
        self,
        executor: AuthorizedDemoExecutor,
        ledger: DemoOrderLedger,
        *,
        intent_id_factory: Callable[[], str] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.executor = executor
        self.ledger = ledger
        self._intent_id_factory = intent_id_factory or (lambda: str(uuid4()))
        self._now = now or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        intent: OrderIntent,
        *,
        internal_before: Mapping[str, Any],
        internal_after: Mapping[str, Any],
    ) -> ControlledDemoExecutionResult:
        intent_id = self._intent_id_factory()
        normalized = self.executor.preflight.validate(intent, environment="demo")
        self.executor.preflight.validate_state(internal_before)
        self.executor.preflight.validate_state(internal_after)
        record = self.ledger.create(
            intent_id,
            normalized.symbol,
            normalized.side,
            normalized.quantity,
            now=self._now(),
        )
        try:
            self.ledger.transition(intent_id, "AUTHORIZED", now=self._now())
            execution = self.executor.execute(
                normalized,
                internal_before=internal_before,
                internal_after=internal_after,
            )
            broker_execution = execution.execution
            order_id = _first_value(broker_execution, "order_id")
            deal_id = _first_value(broker_execution, "deal_id", "execution_id")
            final_state = _final_state(broker_execution)
            record = self.ledger.transition(
                intent_id,
                final_state,
                now=self._now(),
                order_id=order_id,
                deal_id=deal_id,
                execution=broker_execution,
            )
            return ControlledDemoExecutionResult(record=record, execution=execution)
        except Exception as exc:
            current = self.ledger.get(intent_id)
            if current.state not in self.ledger.TERMINAL_STATES:
                try:
                    record = self.ledger.transition(intent_id, "FAILED", now=self._now(), error=str(exc))
                except Exception:
                    record = self.ledger.get(intent_id)
            else:
                record = current
            raise


def _first_value(data: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def _final_state(execution: Mapping[str, Any]) -> str:
    status = str(execution.get("status", "accepted")).strip().lower()
    if status in {"rejected", "reject"}:
        return "REJECTED"
    if status in {"failed", "error"}:
        return "FAILED"
    if status in {"filled", "done", "closed"}:
        return "FILLED"
    # A broker response that does not explicitly confirm a fill remains
    # SUBMITTED so recovery can reconcile it instead of assuming success.
    return "SUBMITTED"
