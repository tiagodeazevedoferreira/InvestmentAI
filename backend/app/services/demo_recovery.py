from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .demo_ledger import DemoOrderLedger, DemoOrderRecord


@dataclass(frozen=True)
class DemoRecoveryResult:
    checked: int
    filled: int
    unresolved: int


class DemoExecutionRecovery:
    """Reconcile durable SUBMITTED orders without issuing new broker orders.

    Recovery is deliberately conservative: only an externally observed deal
    can move an order to FILLED. Ambiguous orders remain SUBMITTED for manual
    investigation rather than being retried automatically.
    """

    def __init__(self, ledger: DemoOrderLedger):
        self.ledger = ledger

    def reconcile_snapshot(self, snapshot: Mapping[str, Any], *, now: datetime | None = None) -> DemoRecoveryResult:
        executions = snapshot.get("executions", [])
        if not isinstance(executions, list):
            raise ValueError("external executions must be a list")
        execution_ids = {
            str(item.get("execution_id"))
            for item in executions
            if isinstance(item, Mapping) and item.get("execution_id")
        }
        deal_ids = {
            str(item.get("deal_id"))
            for item in executions
            if isinstance(item, Mapping) and item.get("deal_id")
        }
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        checked = filled = unresolved = 0
        for record in self.ledger.pending():
            if record.state != "SUBMITTED":
                continue
            checked += 1
            if record.deal_id and (record.deal_id in execution_ids or record.deal_id in deal_ids):
                self.ledger.transition(record.intent_id, "FILLED", now=timestamp)
                filled += 1
            else:
                unresolved += 1
        return DemoRecoveryResult(checked=checked, filled=filled, unresolved=unresolved)
