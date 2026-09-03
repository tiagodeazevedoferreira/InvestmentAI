from datetime import datetime

import pandas as pd

from backend.app.services.paper_ledger import PaperDecisionLedger
from backend.app.services.paper_scheduler import b3_session_allowed, signal_id, yahoo_symbol


class FakeFirebase:
    enabled = True

    def __init__(self):
        self.data = {}

    def get(self, path):
        return self.data.get(path)

    def set(self, path, value):
        self.data[path] = value


def test_yahoo_symbol_normalization():
    assert yahoo_symbol("PETR4") == "PETR4.SA"
    assert yahoo_symbol("petr4.sa") == "PETR4.SA"


def test_signal_id_is_deterministic():
    value = signal_id("PETR4", "2026-09-03T20:00:00+00:00", "BUY")
    assert value == signal_id("petr4", "2026-09-03T20:00:00+00:00", "BUY")
    assert value != signal_id("PETR4", "2026-09-04T20:00:00+00:00", "BUY")


def test_b3_scheduler_guard_allows_post_close_weekday():
    allowed, reason = b3_session_allowed(datetime.fromisoformat("2026-09-03T18:00:00-03:00"))
    assert allowed is True
    assert "passed" in reason


def test_b3_scheduler_guard_rejects_weekend():
    allowed, reason = b3_session_allowed(datetime.fromisoformat("2026-09-05T18:00:00-03:00"))
    assert allowed is False
    assert "weekend" in reason


def test_ledger_claim_is_idempotent():
    firebase = FakeFirebase()
    ledger = PaperDecisionLedger(firebase=firebase)
    kwargs = {
        "symbol": "PETR4",
        "bar_timestamp": "2026-09-03T20:00:00+00:00",
        "action": "BUY",
    }
    first, record = ledger.claim("abc123", **kwargs)
    second, existing = ledger.claim("abc123", **kwargs)
    assert first is True
    assert second is False
    assert existing == record


def test_bar_timestamp_source_is_datetime_index():
    frame = pd.DataFrame({"Close": [10.0]}, index=pd.to_datetime(["2026-09-03"]))
    assert frame.index[0].tz is None
