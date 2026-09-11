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


def test_ledger_finds_filled_match_for_duplicate_guard(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, order_id="order-1", deal_id="deal-1")
    filled = ledger.transition("intent-1", "FILLED", now=NOW, order_id="order-1", deal_id="deal-1")

    match = ledger.find_filled_match("eurusd", "buy", 0.01)
    assert match == filled


def test_ledger_does_not_treat_failed_or_rejected_as_duplicate(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")

    ledger.create("rejected", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("rejected", "AUTHORIZED", now=NOW)
    ledger.transition("rejected", "REJECTED", now=NOW)

    ledger.create("failed", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("failed", "AUTHORIZED", now=NOW)
    ledger.transition("failed", "FAILED", now=NOW)

    assert ledger.find_filled_match("EURUSD", "BUY", 0.01) is None


def test_ledger_recovers_submitted_only_with_matching_deal(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition(
        "intent-1", "SUBMITTED", now=NOW,
        order_id="order-1", deal_id="deal-1",
        execution={"order_id": "order-1", "deal_id": "deal-1", "status": "accepted"},
    )

    recovered = ledger.recover_submitted(
        "intent-1",
        {"executions": [{"execution_id": "deal-1", "order_id": "order-1", "symbol": "EURUSD", "quantity": 0.01}]},
        now=NOW,
    )

    assert recovered.state == "FILLED"
    assert recovered.order_id == "order-1"
    assert recovered.deal_id == "deal-1"


def test_ledger_keeps_submitted_when_deal_evidence_is_missing(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, order_id="order-1", deal_id="deal-1")

    recovered = ledger.recover_submitted(
        "intent-1",
        {"executions": [], "open_orders": [{"order_id": "order-1", "symbol": "EURUSD"}]},
        now=NOW,
    )

    assert recovered.state == "SUBMITTED"
    assert recovered.deal_id == "deal-1"
