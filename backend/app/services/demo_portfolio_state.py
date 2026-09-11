from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class DemoPortfolioStateError(RuntimeError):
    """Raised when the application DEMO portfolio state cannot be safely read or updated."""


class DemoPortfolioStateStore:
    """Persistent application-owned mirror of the DEMO portfolio/account state.

    The store is the application's internal state provider used by DEMO
    authorization/reconciliation. Broker snapshots are accepted only through
    explicit bootstrap/synchronization methods; callers never read broker state
    directly as the internal state during reconciliation.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_portfolio_state (
                    state_id INTEGER PRIMARY KEY CHECK (state_id = 1),
                    updated_at TEXT NOT NULL,
                    state_json TEXT NOT NULL
                )
                """
            )

    def exists(self) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM demo_portfolio_state WHERE state_id = 1"
            ).fetchone()
        return row is not None

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM demo_portfolio_state WHERE state_id = 1"
            ).fetchone()
        if row is None:
            raise DemoPortfolioStateError("application DEMO portfolio state is not initialized")
        try:
            value = json.loads(row["state_json"])
        except json.JSONDecodeError as exc:
            raise DemoPortfolioStateError("application DEMO portfolio state is corrupted") from exc
        if not isinstance(value, dict):
            raise DemoPortfolioStateError("application DEMO portfolio state must be a mapping")
        return dict(value)

    def bootstrap(self, external_snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """Initialize application state from one explicitly captured broker snapshot."""
        if self.exists():
            return self.snapshot()
        return self.synchronize(external_snapshot)

    def synchronize(self, external_snapshot: Mapping[str, Any]) -> dict[str, Any]:
        """Persist a validated external snapshot as the application's current state."""
        state = self._normalize(external_snapshot)
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO demo_portfolio_state (state_id, updated_at, state_json)
                VALUES (1, ?, ?)
                ON CONFLICT(state_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    state_json = excluded.state_json
                """,
                (updated_at, json.dumps(state, sort_keys=True)),
            )
        return dict(state)

    @staticmethod
    def _normalize(snapshot: Mapping[str, Any]) -> dict[str, Any]:
        try:
            cash = float(snapshot["cash"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DemoPortfolioStateError("DEMO portfolio state requires numeric cash") from exc
        if cash < 0:
            raise DemoPortfolioStateError("DEMO portfolio cash cannot be negative")

        positions = snapshot.get("positions", {})
        open_orders = snapshot.get("open_orders", [])
        executions = snapshot.get("executions", [])
        if not isinstance(positions, Mapping):
            raise DemoPortfolioStateError("positions must be a mapping")
        if not isinstance(open_orders, list):
            raise DemoPortfolioStateError("open_orders must be a list")
        if not isinstance(executions, list):
            raise DemoPortfolioStateError("executions must be a list")

        normalized_positions: dict[str, Any] = {}
        for symbol, position in positions.items():
            key = str(symbol).strip().upper()
            if not key:
                raise DemoPortfolioStateError("position symbol cannot be empty")
            if isinstance(position, Mapping):
                quantity = float(position.get("quantity", 0.0))
                normalized = dict(position)
                normalized["quantity"] = quantity
            else:
                quantity = float(position)
                normalized = {"quantity": quantity}
            if quantity < 0:
                raise DemoPortfolioStateError(f"position quantity cannot be negative: {key}")
            normalized_positions[key] = normalized

        return {
            "cash": cash,
            "positions": normalized_positions,
            "open_orders": [dict(item) for item in open_orders if isinstance(item, Mapping)],
            "executions": [dict(item) for item in executions if isinstance(item, Mapping)],
        }
