from __future__ import annotations

from backend.app.services.paper_ledger import PaperDecisionLedger
from backend.app.services.paper_outcomes import OutcomeObservation


class FakeFirebase:
    enabled = True

    def __init__(self):
        self.values = {}
        self.set_calls = 0

    def get(self, path):
        return self.values.get(path)

    def set(self, path, value):
        self.set_calls += 1
        self.values[path] = value

    def list_children(self, path, limit=200):
        return list(self.values.values())[:limit]


def _observation() -> OutcomeObservation:
    return OutcomeObservation(
        "sig", "PETR4", "BUY", "2026-09-01T00:00:00+00:00",
        100.0, 1, "2026-09-02T00:00:00+00:00",
        102.0, 0.02, 0.02, True,
    )


def test_claim_persists_decision_price():
    firebase = FakeFirebase()
    ledger = PaperDecisionLedger(firebase=firebase)

    created, record = ledger.claim(
        "sig",
        symbol="PETR4",
        bar_timestamp="2026-09-01T00:00:00+00:00",
        action="BUY",
        decision_price=100.0,
    )

    assert created is True
    assert record["decision_price"] == 100.0
    assert firebase.values["paper/decision_ledger/sig"]["decision_price"] == 100.0


def test_save_outcomes_is_idempotent_for_identical_payload():
    firebase = FakeFirebase()
    ledger = PaperDecisionLedger(firebase=firebase)
    ledger.claim(
        "sig",
        symbol="PETR4",
        bar_timestamp="2026-09-01T00:00:00+00:00",
        action="BUY",
        decision_price=100.0,
    )
    observation = _observation()

    first = ledger.save_outcomes("sig", [observation])
    first_updated_at = first["outcomes_updated_at"]
    first_set_calls = firebase.set_calls

    second = ledger.save_outcomes("sig", [observation])

    assert second["outcomes"] == first["outcomes"]
    assert second["outcomes_updated_at"] == first_updated_at
    assert firebase.set_calls == first_set_calls
