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
                    execution_json TEXT)"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_demo_orders_state ON demo_orders(state)")

    def create(self, intent_id: str, symbol: str, side: str, quantity: float, *, now: datetime | None = None) -> DemoOrderRecord:
        intent_id, symbol, side, quantity = intent_id.strip(), symbol.strip().upper(), side.strip().upper(), float(quantity)
        if not intent_id: raise ValueError("intent_id is required")
        if not symbol: raise ValueError("symbol is required")
        if side not in {"BUY", "SELL"}: raise ValueError("side must be BUY or SELL")
        if quantity <= 0: raise ValueError("quantity must be positive")
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO demo_orders(intent_id,symbol,side,quantity,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (intent_id, symbol, side, quantity, "INTENDED", timestamp, timestamp),
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
        )

    def find_terminal_match(self, symbol: str, side: str, quantity: float) -> DemoOrderRecord | None:
        """Return the newest terminal record with the exact controlled intent shape.

        This is a conservative duplicate guard for explicitly controlled DEMO
        runs. It prevents a rerun of the same symbol/side/quantity from blindly
        submitting a second order after a prior successful execution.
        """
        symbol = symbol.strip().upper()
        side = side.strip().upper()
        quantity = float(quantity)
        with self._connect() as connection:
            row = connection.execute(
                """SELECT intent_id FROM demo_orders
                   WHERE symbol=? AND side=? AND quantity=?
                     AND state IN ('FILLED','REJECTED','FAILED')
                   ORDER BY updated_at DESC LIMIT 1""",
                (symbol, side, quantity),
            ).fetchone()
        return self.get(row["intent_id"]) if row is not None else None

    def pending(self) -> tuple[DemoOrderRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT intent_id FROM demo_orders WHERE state NOT IN ('FILLED','REJECTED','FAILED') ORDER BY created_at").fetchall()
        return tuple(self.get(row["intent_id"]) for row in rows)
