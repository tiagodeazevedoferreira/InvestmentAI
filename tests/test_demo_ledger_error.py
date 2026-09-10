from datetime import datetime, timezone

from app.services.demo_ledger import DemoOrderLedger


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def test_record_error_does_not_change_lifecycle_state(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, deal_id="456")

    record = ledger.record_error("intent-1", "post reconciliation unavailable", now=NOW)

    assert record.state == "SUBMITTED"
    assert record.deal_id == "456"
    assert record.error == "post reconciliation unavailable"
