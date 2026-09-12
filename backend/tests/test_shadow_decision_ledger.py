from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.paper_execution import PaperAccount
from app.services.paper_ledger import PaperDecisionLedger
from app.services.paper_scheduler import run_symbol
from app.services.shadow_decision_ledger import (
    ShadowDecisionLedger,
    ShadowDecisionLedgerError,
    shadow_decision_id,
)


class InMemoryFirebase:
    def __init__(self, *, enabled: bool = True) -> None:
        self.enabled = enabled
        self.values: dict[str, dict] = {}
        self.set_calls = 0

    def get(self, path: str):
        value = self.values.get(path.strip("/"))
        return deepcopy(value) if value is not None else None

    def set(self, path: str, value: dict) -> None:
        self.set_calls += 1
        self.values[path.strip("/")] = deepcopy(value)

    def list_children(self, path: str, *, limit: int = 200) -> list[dict]:
        prefix = f"{path.strip('/')}/"
        return [
            deepcopy(value)
            for key, value in self.values.items()
            if key.startswith(prefix) and "/" not in key[len(prefix) :]
        ][-limit:]


def record_kwargs(**overrides):
    values = {
        "source": "paper_scheduler",
        "policy": "rsi14_threshold",
        "symbol": "PETR4",
        "event_timestamp": "2026-09-11T20:30:00+00:00",
        "action": "BUY",
        "quantity": 12,
        "reference_price": 31.5,
        "signal": {"rsi14": 22.1},
        "risk": {"allowed": True, "reason": "within cap"},
    }
    values.update(overrides)
    return values


def test_shadow_id_is_deterministic_for_equivalent_event_timestamp():
    identity = {
        key: value
        for key, value in record_kwargs().items()
        if key in {"source", "policy", "symbol", "event_timestamp", "action"}
    }
    expected = shadow_decision_id(**identity)
    assert expected == shadow_decision_id(
        **{
            **identity,
            "symbol": "PETR4.SA",
            "action": "buy",
            "event_timestamp": "2026-09-11T17:30:00-03:00",
        }
    )


def test_record_preserves_observational_context_and_can_be_read():
    firebase = InMemoryFirebase()
    ledger = ShadowDecisionLedger(firebase=firebase)

    created, record = ledger.record(**record_kwargs())

    assert created is True
    assert record["execution_authority"] == "none"
    assert record["state"] == "recorded"
    assert record["symbol"] == "PETR4"
    assert record["quantity"] == 12.0
    assert record["reference_price"] == 31.5
    assert record["signal"] == {"rsi14": 22.1}
    assert record["risk"]["allowed"] is True
    assert "intent" not in record
    assert ledger.get(record["shadow_id"]) == record


def test_record_is_idempotent_and_retains_first_observation():
    firebase = InMemoryFirebase()
    ledger = ShadowDecisionLedger(firebase=firebase)

    created, first = ledger.record(**record_kwargs())
    repeated, second = ledger.record(**record_kwargs(quantity=0, risk={"allowed": False}))

    assert created is True
    assert repeated is False
    assert second == first
    assert firebase.set_calls == 1


def test_list_records_filters_by_symbol_and_orders_newest_event_first():
    ledger = ShadowDecisionLedger(firebase=InMemoryFirebase())
    ledger.record(**record_kwargs(event_timestamp="2026-09-10T20:30:00+00:00"))
    _, newest = ledger.record(**record_kwargs(event_timestamp="2026-09-11T20:30:00+00:00", action="HOLD"))
    ledger.record(**record_kwargs(symbol="VALE3", action="SELL"))

    records = ledger.list_records(symbol="PETR4.SA")

    assert records[0]["shadow_id"] == newest["shadow_id"]
    assert len(records) == 2


def test_ledger_fails_closed_when_persistence_is_unavailable_or_input_is_ambiguous():
    ledger = ShadowDecisionLedger(firebase=InMemoryFirebase(enabled=False))
    with pytest.raises(ShadowDecisionLedgerError, match="Firebase"):
        ledger.record(**record_kwargs())

    enabled_ledger = ShadowDecisionLedger(firebase=InMemoryFirebase())
    with pytest.raises(ValueError, match="timezone"):
        enabled_ledger.record(**record_kwargs(event_timestamp="2026-09-11T20:30:00"))
    with pytest.raises(ValueError, match="finite"):
        enabled_ledger.record(**record_kwargs(reference_price=float("nan")))


def test_ledger_surfaces_persistence_failure_without_creating_a_record():
    class FailingFirebase(InMemoryFirebase):
        def set(self, path: str, value: dict) -> None:
            raise RuntimeError("storage unavailable")

    ledger = ShadowDecisionLedger(firebase=FailingFirebase())
    with pytest.raises(ShadowDecisionLedgerError, match="persistence"):
        ledger.record(**record_kwargs())


class StaticProvider:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def history(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        return self.frame.copy()


class AccountStore:
    def __init__(self) -> None:
        self.account = PaperAccount(initial_cash=100_000)
        self.settings = SimpleNamespace(paper_max_order_notional=10_000)
        self.save_calls = 0

    def get(self) -> PaperAccount:
        return self.account

    def save(self) -> None:
        self.save_calls += 1


def test_scheduler_records_shadow_decision_without_paper_execution():
    close = [100 - number for number in range(40)]
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": close,
            "Low": close,
            "Close": close,
            "Volume": [1_000] * len(close),
        },
        index=pd.date_range("2026-07-01", periods=40, tz="UTC"),
    )
    firebase = InMemoryFirebase()
    account_store = AccountStore()
    shadow_ledger = ShadowDecisionLedger(firebase=firebase)

    result = run_symbol(
        StaticProvider(frame),
        account_store,
        PaperDecisionLedger(firebase=firebase),
        "PETR4",
        execute=False,
        shadow_ledger=shadow_ledger,
    )

    assert result.status == "decided"
    assert result.shadow_id
    record = shadow_ledger.get(result.shadow_id)
    assert record is not None
    assert record["execution_authority"] == "none"
    assert account_store.account.orders == []
    assert account_store.save_calls == 0
