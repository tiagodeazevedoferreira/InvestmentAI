from datetime import datetime, timezone

import pytest

from app.services.demo_ledger import DemoLedgerError, DemoOrderLedger


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def test_ledger_persists_and_recovers_record(tmp_path):
    path = tmp_path / "demo.sqlite3"
    ledger = DemoOrderLedger(path)
    created = ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    assert created.state == "INTENDED"

    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition(
        "intent-1",
        "SUBMITTED",
        now=NOW,
        order_id="order-1",
        deal_id="deal-1",
        execution={"order_id": "order-1", "deal_id": "deal-1", "status": "accepted"},
    )

    reopened = DemoOrderLedger(path)
    record = reopened.get("intent-1")
    assert record.state == "SUBMITTED"
    assert record.order_id == "order-1"
    assert record.deal_id == "deal-1"
    assert record.execution["status"] == "accepted"


def test_ledger_rejects_invalid_transition(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    with pytest.raises(DemoLedgerError, match="invalid DEMO order transition"):
        ledger.transition("intent-1", "FILLED", now=NOW)


def test_ledger_rejects_duplicate_intent(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    with pytest.raises(DemoLedgerError, match="already exists"):
        ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
