from __future__ import annotations

import json
from threading import RLock
from typing import Any

from ..firebase import FirebaseRepository
from ..settings import get_settings
from .paper_execution import PaperAccount, PaperPosition


class PaperAccountStore:
    """Durable paper-account state with a bounded Firebase footprint."""

    def __init__(self, firebase: FirebaseRepository | None = None):
        self.settings = get_settings()
        self.firebase = firebase or FirebaseRepository(
            self.settings.firebase_database_url,
            self.settings.firebase_service_account,
        )
        self.path = self.settings.paper_account_path.strip("/")
        self._lock = RLock()
        self._account: PaperAccount | None = None

    def get(self) -> PaperAccount:
        with self._lock:
            if self._account is not None:
                return self._account
            persisted = self.firebase.get(self.path) if self.firebase.enabled else None
            if persisted:
                self._account = self._from_dict(persisted)
            else:
                self._account = self._new_account()
                self.save()
            return self._account

    def save(self) -> dict:
        with self._lock:
            account = self._account or self._new_account()
            self._account = account
            payload = account.snapshot()
            # Keep the Firebase document bounded. Full audit history remains
            # available in-process/backtest logs, while RTDB stores recent state.
            payload["recent_orders"] = account.orders[-100:]
            payload["recent_executions"] = account.executions[-100:]
            payload.pop("open_orders", None)
            if self.firebase.enabled:
                raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
                if len(raw.encode("utf-8")) > self.settings.max_firebase_write_bytes:
                    raise RuntimeError("paper account snapshot exceeds Firebase write limit")
                self.firebase.set(self.path, payload)
            return payload

    def reset(self, initial_cash: float | None = None) -> dict:
        with self._lock:
            cash = initial_cash if initial_cash is not None else self.settings.paper_initial_cash
            self._account = PaperAccount(
                initial_cash=cash,
                fee_bps=self.settings.paper_fee_bps,
                slippage_bps=self.settings.paper_slippage_bps,
            )
            return self.save()

    def _new_account(self) -> PaperAccount:
        return PaperAccount(
            initial_cash=self.settings.paper_initial_cash,
            fee_bps=self.settings.paper_fee_bps,
            slippage_bps=self.settings.paper_slippage_bps,
        )

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> PaperAccount:
        account = PaperAccount(
            initial_cash=float(data.get("initial_cash", 100_000.0)),
            fee_bps=float(data.get("fee_bps", 5.0)),
            slippage_bps=float(data.get("slippage_bps", 5.0)),
            cash=float(data.get("cash", data.get("initial_cash", 100_000.0))),
            realized_pnl=float(data.get("realized_pnl", 0.0)),
        )
        positions = data.get("positions", {})
        account.positions = {
            symbol: PaperPosition(
                symbol=symbol,
                quantity=int(value.get("quantity", 0)),
                average_price=float(value.get("average_price", 0.0)),
                market_price=float(value.get("market_price", 0.0)),
            )
            for symbol, value in positions.items()
            if int(value.get("quantity", 0)) > 0
        }
        account.orders = list(data.get("recent_orders", []))
        account.executions = list(data.get("recent_executions", []))
        return account
