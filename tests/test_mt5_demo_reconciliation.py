from __future__ import annotations

from datetime import datetime, timezone

from app.services.mt5_demo import MT5DemoBroker


class SnapshotGateway:
    def account_info(self):
        return {"login": 123, "server": "Doto-Demo", "balance": 10000, "equity": 10100, "currency": "USD", "trade_allowed": True}

    def positions_get(self):
        return [{"ticket": 10, "symbol": "PETR4", "volume": 2, "type": 0, "price_open": 90}]

    def orders_get(self):
        return [{"ticket": 20, "symbol": "PETR4", "volume_current": 1, "type": 2, "state": 1}]

    def history_deals_get(self, date_from, date_to):
        return [{"ticket": 30, "order": 20, "symbol": "PETR4", "volume": 1, "price": 100, "time": 123}]


def test_reconciliation_snapshot_matches_operational_contract():
    broker = MT5DemoBroker(SnapshotGateway())
    snapshot = broker.reconciliation_snapshot(
        datetime(2026, 9, 2, tzinfo=timezone.utc),
        datetime(2026, 9, 3, tzinfo=timezone.utc),
    )
    assert snapshot["cash"] == 10000
    assert snapshot["positions"]["PETR4"]["quantity"] == 2
    assert snapshot["open_orders"][0]["order_id"] == "20"
    assert snapshot["executions"][0]["execution_id"] == "30"
    assert "captured_at" in snapshot
