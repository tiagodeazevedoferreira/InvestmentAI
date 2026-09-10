from datetime import datetime, timezone

from app.services.demo_ledger import DemoOrderLedger
from app.services.demo_recovery import DemoExecutionRecovery


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def test_recovery_marks_only_observed_deals_as_filled(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, deal_id="deal-1")

    result = DemoExecutionRecovery(ledger).reconcile_snapshot(
        {"executions": [{"execution_id": "deal-1"}]}, now=NOW
    )

    assert result == type(result)(checked=1, filled=1, unresolved=0)
    assert ledger.get("intent-1").state == "FILLED"


def test_recovery_does_not_guess_when_deal_is_missing(tmp_path):
    ledger = DemoOrderLedger(tmp_path / "demo.sqlite3")
    ledger.create("intent-1", "EURUSD", "BUY", 0.01, now=NOW)
    ledger.transition("intent-1", "AUTHORIZED", now=NOW)
    ledger.transition("intent-1", "SUBMITTED", now=NOW, deal_id="deal-1")

    result = DemoExecutionRecovery(ledger).reconcile_snapshot({"executions": []}, now=NOW)

    assert result.checked == 1
    assert result.filled == 0
    assert result.unresolved == 1
    assert ledger.get("intent-1").state == "SUBMITTED"
