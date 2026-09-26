from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class DemoLedgerError(RuntimeError):
    """Raised when the DEMO execution ledger cannot safely persist state."""


@dataclass(frozen=True)
class DemoOrderRecord:
    intent_id: str
    symbol: str
    side: str
    quantity: float
    state: str
    created_at: str
    updated_at: str
    order_id: str | None = None
    deal_id: str | None = None
    error: str | None = None
    execution: Mapping[str, Any] | None = None
    correlation_id: str | None = None


class DemoOrderLedger:
    """Small durable, broker-independent SQLite ledger for DEMO order lifecycle."""

    VALID_STATES = frozenset({"INTENDED", "AUTHORIZED", "SUBMITTED", "FILLED", "REJECTED", "FAILED"})
    TERMINAL_STATES = frozenset({"FILLED", "REJECTED", "FAILED"})
    ALLOWED_TRANSITIONS = {
        "INTENDED": frozenset({"AUTHORIZED", "FAILED"}),
        "AUTHORIZED": frozenset({"SUBMITTED", "REJECTED", "FAILED"}),
        "SUBMITTED": frozenset({"FILLED", "REJECTED", "FAILED"}),
        "FILLED": frozenset(), "REJECTED": frozenset(), "FAILED": frozenset(),
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS demo_orders (
                    intent_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL,
                    quantity REAL NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, order_id TEXT, deal_id TEXT, error TEXT,
                    execution_json TEXT, correlation_id TEXT)"""
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(demo_orders)")}
            if "correlation_id" not in columns:
                connection.execute("ALTER TABLE demo_orders ADD COLUMN correlation_id TEXT")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_demo_orders_state ON demo_orders(state)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_demo_orders_correlation ON demo_orders(correlation_id)")

    def create(self, intent_id: str, symbol: str, side: str, quantity: float, *,
               correlation_id: str | None = None, now: datetime | None = None) -> DemoOrderRecord:
        intent_id, symbol, side, quantity = intent_id.strip(), symbol.strip().upper(), side.strip().upper(), float(quantity)
        correlation_id = correlation_id.strip() if correlation_id else None
        if not intent_id: raise ValueError("intent_id is required")
        if not symbol: raise ValueError("symbol is required")
        if side not in {"BUY", "SELL"}: raise ValueError("side must be BUY or SELL")
        if quantity <= 0: raise ValueError("quantity must be positive")
        if correlation_id is not None and not correlation_id: raise ValueError("correlation_id cannot be empty")
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO demo_orders(intent_id,symbol,side,quantity,state,created_at,updated_at,correlation_id) VALUES(?,?,?,?,?,?,?,?)",
                    (intent_id, symbol, side, quantity, "INTENDED", timestamp, timestamp, correlation_id),
                )
        except sqlite3.IntegrityError as exc:
            raise DemoLedgerError(f"intent_id already exists: {intent_id}") from exc
        return self.get(intent_id)

    def transition(self, intent_id: str, new_state: str, *, now: datetime | None = None,
                   order_id: str | None = None, deal_id: str | None = None,
                   error: str | None = None, execution: Mapping[str, Any] | None = None) -> DemoOrderRecord:
        new_state = new_state.strip().upper()
        if new_state not in self.VALID_STATES: raise DemoLedgerError(f"invalid DEMO order state: {new_state}")
        current = self.get(intent_id)
        if new_state not in self.ALLOWED_TRANSITIONS[current.state]:
            raise DemoLedgerError(f"invalid DEMO order transition: {current.state} -> {new_state}")
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        execution_json = json.dumps(dict(execution), sort_keys=True, default=str) if execution is not None else None
        with self._connect() as connection:
            connection.execute(
                """UPDATE demo_orders SET state=?, updated_at=?, order_id=COALESCE(?,order_id),
                   deal_id=COALESCE(?,deal_id), error=?, execution_json=COALESCE(?,execution_json)
                   WHERE intent_id=?""",
                (new_state, timestamp, order_id, deal_id, error, execution_json, intent_id),
            )
        return self.get(intent_id)

    def record_error(self, intent_id: str, error: str, *, now: datetime | None = None) -> DemoOrderRecord:
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute("UPDATE demo_orders SET error=?, updated_at=? WHERE intent_id=?", (str(error), timestamp, intent_id))
        return self.get(intent_id)

    def get(self, intent_id: str) -> DemoOrderRecord:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM demo_orders WHERE intent_id=?", (intent_id,)).fetchone()
        if row is None: raise DemoLedgerError(f"unknown DEMO intent_id: {intent_id}")
        execution = json.loads(row["execution_json"]) if row["execution_json"] else None
        return DemoOrderRecord(
            intent_id=row["intent_id"], symbol=row["symbol"], side=row["side"], quantity=float(row["quantity"]),
            state=row["state"], created_at=row["created_at"], updated_at=row["updated_at"],
            order_id=row["order_id"], deal_id=row["deal_id"], error=row["error"], execution=execution,
            correlation_id=row["correlation_id"],
        )

    def find_filled_match(self, symbol: str, side: str, quantity: float) -> DemoOrderRecord | None:
        """Return the newest filled record matching a controlled intent shape.

        Only FILLED orders are treated as duplicates. Known REJECTED/FAILED
        outcomes remain retryable because no successful broker execution exists.
        """
        symbol = symbol.strip().upper()
        side = side.strip().upper()
        quantity = float(quantity)
        with self._connect() as connection:
            row = connection.execute(
                """SELECT intent_id FROM demo_orders
                   WHERE symbol=? AND side=? AND quantity=? AND state='FILLED'
                   ORDER BY updated_at DESC LIMIT 1""",
                (symbol, side, quantity),
            ).fetchone()
        return self.get(row["intent_id"]) if row is not None else None

    def recover_submitted(self, intent_id: str, external: Mapping[str, Any], *, now: datetime | None = None) -> DemoOrderRecord:
        """Recover a SUBMITTED order only when broker deal evidence is explicit.

        A matching deal ID is sufficient to promote SUBMITTED -> FILLED. An
        open order or a position alone is intentionally insufficient because it
        does not prove that this exact intent was executed. Missing evidence
        leaves the order SUBMITTED and therefore non-retryable by this method.
        """
        current = self.get(intent_id)
        if current.state != "SUBMITTED":
            return current

        executions = external.get("executions", [])
        if not isinstance(executions, list):
            return current

        for item in executions:
            if not isinstance(item, Mapping):
                continue
            execution_id = item.get("execution_id")
            if current.deal_id and execution_id and str(current.deal_id) == str(execution_id):
                return self.transition(
                    intent_id, "FILLED", now=now,
                    order_id=_first_value(item, "order_id", "order"),
                    deal_id=str(execution_id),
                    execution=item,
                )
            correlation = item.get("correlation_id")
            if not current.correlation_id or not correlation:
                continue
            if str(correlation).strip().upper() != str(current.correlation_id).strip().upper():
                continue
            if str(item.get("symbol", "")).strip().upper() != current.symbol:
                continue
            if str(item.get("side", "")).strip().upper() != current.side:
                continue
            try:
                if abs(float(item.get("quantity", 0.0)) - current.quantity) > 1e-12:
                    continue
            except (TypeError, ValueError):
                continue
            return self.transition(
                intent_id, "FILLED", now=now,
                order_id=_first_value(item, "order_id", "order"),
                deal_id=str(execution_id) if execution_id else None,
                execution=item,
            )

        return current

    def pending(self) -> tuple[DemoOrderRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT intent_id FROM demo_orders WHERE state NOT IN ('FILLED','REJECTED','FAILED') ORDER BY created_at").fetchall()
        return tuple(self.get(row["intent_id"]) for row in rows)


def _first_value(data: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip() and str(value) != "0":
            return str(value)
    return None
