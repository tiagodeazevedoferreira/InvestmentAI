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

    This service is manual-call only. It has no scheduler hook, no signal
    generation, and no automatic retry. If broker outcome is uncertain, the
    ledger remains recoverable instead of guessing that an order failed.
    """

    def __init__(self, executor: AuthorizedDemoExecutor, ledger: DemoOrderLedger, *,
                 intent_id_factory: Callable[[], str] | None = None,
                 now: Callable[[], datetime] | None = None) -> None:
        self.executor = executor
        self.ledger = ledger
        self._intent_id_factory = intent_id_factory or (lambda: str(uuid4()))
        self._now = now or (lambda: datetime.now(timezone.utc))

    def execute(self, intent: OrderIntent, *, internal_before: Mapping[str, Any],
                internal_after_provider: Callable[[], Mapping[str, Any]]) -> ControlledDemoExecutionResult:
        intent_id = self._intent_id_factory()
        normalized = self.executor.preflight.validate(intent, environment="demo")
        self.executor.preflight.validate_state(internal_before)
        self.ledger.create(intent_id, normalized.symbol, normalized.side, normalized.quantity, now=self._now())
        try:
            def mark_authorized() -> None:
                self.ledger.transition(intent_id, "AUTHORIZED", now=self._now())

            def mark_submitted(execution: Mapping[str, Any]) -> None:
                # A broker-level rejection is already a known terminal outcome.
                # Persist it immediately so a later reconciliation/clock error
                # cannot incorrectly leave the order in SUBMITTED/unknown state.
                submission_state = "REJECTED" if _is_known_rejection(execution) else "SUBMITTED"
                self.ledger.transition(intent_id, submission_state, now=self._now(),
                                      order_id=_first_value(execution, "order_id", "order"),
                                      deal_id=_first_value(execution, "deal_id", "deal", "execution_id"),
                                      execution=execution)

            result = self.executor.execute(normalized, internal_before=internal_before,
                                           internal_after_provider=internal_after_provider,
                                           on_authorized=mark_authorized, on_submitted=mark_submitted)
            broker_execution = result.execution
            final_state = _final_state(broker_execution)
            if final_state != self.ledger.get(intent_id).state:
                record = self.ledger.transition(intent_id, final_state, now=self._now(),
                                                order_id=_first_value(broker_execution, "order_id", "order"),
                                                deal_id=_first_value(broker_execution, "deal_id", "deal", "execution_id"),
                                                execution=broker_execution)
            else:
                record = self.ledger.get(intent_id)
            return ControlledDemoExecutionResult(record=record, execution=result)
        except Exception as exc:
            current = self.ledger.get(intent_id)
            if current.state == "INTENDED":
                try:
                    record = self.ledger.transition(intent_id, "FAILED", now=self._now(), error=str(exc))
                except Exception:
                    record = self.ledger.get(intent_id)
            elif current.state == "AUTHORIZED":
                # Authorization is the last local state before broker submission.
                # If submission then raises, the broker outcome is unknowable: the
                # request may have reached MT5 even though no response was received.
                # Preserve it as recoverable SUBMITTED/uncertain; never classify it
                # as FAILED and never retry automatically.
                record = self.ledger.transition(intent_id, "SUBMITTED", now=self._now(), error=str(exc))
            else:
                record = self.ledger.record_error(intent_id, str(exc), now=self._now())
            raise

    def recover_pending(self, external_provider: Callable[[DemoOrderRecord], Mapping[str, Any]]) -> tuple[DemoOrderRecord, ...]:
        """Recover durable pending DEMO orders after an application restart.

        Recovery is read-only with respect to the broker: it only inspects
        persisted SUBMITTED records and broker evidence supplied by the caller.
        A record becomes FILLED only when its exact deal ID is externally
        confirmed. No pending record is resubmitted automatically.

        A failure while obtaining evidence for one pending record is itself
        treated as unresolved. The record remains SUBMITTED with the error
        recorded, and recovery continues for the remaining pending records.
        """
        recovered: list[DemoOrderRecord] = []
        for record in self.ledger.pending():
            if record.state != "SUBMITTED":
                recovered.append(record)
                continue
            try:
                external = external_provider(record)
                recovered.append(self.ledger.recover_submitted(record.intent_id, external, now=self._now()))
            except Exception as exc:
                recovered.append(self.ledger.record_error(record.intent_id, str(exc), now=self._now()))
        return tuple(recovered)


def _first_value(data: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip() and str(value) != "0": return str(value)
    return None


def _is_known_rejection(execution: Mapping[str, Any]) -> bool:
    status = str(execution.get("status", "")).strip().lower()
    if status in {"rejected", "reject", "failed", "error"}:
        return True
    return execution.get("accepted") is False


def _final_state(execution: Mapping[str, Any]) -> str:
    status = str(execution.get("status", "")).strip().lower()
    if status in {"rejected", "reject"}: return "REJECTED"
    if status in {"failed", "error"}: return "FAILED"
    retcode = execution.get("retcode")
    if retcode is not None:
        try:
            code = int(retcode)
            if code == 10009: return "FILLED"
            if code == 10008: return "SUBMITTED"
        except (TypeError, ValueError):
            pass
    if status in {"filled", "done", "closed"}: return "FILLED"
    if execution.get("accepted") is False: return "REJECTED"
    return "SUBMITTED"
