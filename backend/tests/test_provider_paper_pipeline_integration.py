from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.paper_execution import PaperAccount
from app.services.paper_ledger import PaperDecisionLedger
from app.services.paper_scheduler import run_scheduler, run_symbol
from app.services.providers import OpenBBProvider, get_provider
from app.services.scheduler_demo_bridge import SchedulerDemoBridge
from app.services.shadow_decision_ledger import ShadowDecisionLedger


class InMemoryFirebase:
    def __init__(self) -> None:
        self.enabled = True
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


class AccountStore:
    def __init__(self) -> None:
        self.firebase = InMemoryFirebase()
        self.account = PaperAccount(initial_cash=100_000)
        self.settings = SimpleNamespace(paper_max_order_notional=10_000)
        self.save_calls = 0

    def get(self) -> PaperAccount:
        return self.account

    def save(self) -> None:
        self.save_calls += 1


def deterministic_b3_frame() -> pd.DataFrame:
    close = [100 - number for number in range(40)]
    return pd.DataFrame(
        {
            "Open": close,
            "High": close,
            "Low": close,
            "Close": close,
            "Volume": [1_000] * len(close),
        },
        index=pd.date_range("2026-07-01", periods=40, tz="UTC"),
    )


def test_provider_scheduler_paper_shadow_path_is_network_free(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        calls.append((symbol, period))
        return deterministic_b3_frame()

    monkeypatch.setattr(OpenBBProvider, "history", fake_history)

    firebase = InMemoryFirebase()
    account_store = AccountStore()
    paper_ledger = PaperDecisionLedger(firebase=firebase)
    shadow_ledger = ShadowDecisionLedger(firebase=firebase)

    result = run_symbol(
        get_provider("openbb"),
        account_store,
        paper_ledger,
        "PETR4",
        period="3mo",
        execute=False,
        shadow_ledger=shadow_ledger,
    )

    assert calls == [("PETR4.SA", "3mo")]
    assert result.status == "decided"
    assert result.symbol == "PETR4"
    assert result.signal_id
    assert result.shadow_id
    assert result.action in {"BUY", "SELL", "HOLD"}
    assert result.reference_price == 61.0
    assert result.executed is False
    assert account_store.account.orders == []
    assert account_store.save_calls == 0

    paper = paper_ledger.get(result.signal_id)
    shadow = shadow_ledger.get(result.shadow_id)
    assert paper is not None and paper["status"] == "completed"
    assert paper["executed"] is False
    assert shadow is not None and shadow["execution_authority"] == "none"


def test_provider_empty_data_fails_closed_before_decision(monkeypatch):
    class EmptyProvider:
        def history(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
            return pd.DataFrame()

    with pytest.raises(ValueError, match="No market data"):
        run_symbol(
            EmptyProvider(),
            AccountStore(),
            PaperDecisionLedger(firebase=InMemoryFirebase()),
            "PETR4",
            execute=False,
        )


def test_provider_invalid_ohlcv_is_rejected_by_quality_boundary():
    class InvalidProvider:
        def history(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
            return pd.DataFrame(
                {"Close": [42.0]},
                index=pd.to_datetime(["2026-09-11T20:00:00+00:00"]),
            )

    with pytest.raises(ValueError, match="Missing OHLCV columns"):
        run_symbol(
            InvalidProvider(),
            AccountStore(),
            PaperDecisionLedger(firebase=InMemoryFirebase()),
            "PETR4",
            execute=False,
        )


def test_invalid_symbol_fails_closed_without_ledger_write():
    firebase = InMemoryFirebase()

    class Provider:
        def history(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
            raise AssertionError("provider must not be called for an invalid symbol")

    with pytest.raises(ValueError, match="symbol is required"):
        run_symbol(
            Provider(),
            AccountStore(),
            PaperDecisionLedger(firebase=firebase),
            "   ",
            execute=False,
        )

    assert firebase.values == {}


def test_hold_is_recorded_but_demo_promotion_is_blocked(monkeypatch):
    frame = deterministic_b3_frame()

    def fake_evaluate(*args, **kwargs):
        return {
            "decision": {
                "action": "HOLD",
                "quantity": 0,
                "reference_price": 61.0,
                "risk_allowed": True,
                "reason": "deterministic HOLD",
            },
            "executed": False,
            "order": None,
        }

    monkeypatch.setattr("app.services.paper_scheduler.evaluate_paper_signal", fake_evaluate)

    result = run_symbol(
        SimpleNamespace(history=lambda symbol, period="3mo": frame.copy()),
        AccountStore(),
        PaperDecisionLedger(firebase=InMemoryFirebase()),
        "PETR4",
        execute=False,
        demo_bridge=SchedulerDemoBridge(enabled=True, symbol_map={"PETR4": "PETR4"}),
    )

    assert result.status == "decided"
    assert result.action == "HOLD"
    assert result.executed is False
    assert result.demo_plan is not None
    assert result.demo_plan.status == "blocked"
    assert result.demo_plan.intent is None
    assert "BUY or SELL" in result.demo_plan.reason


def test_duplicate_decision_is_idempotent_across_paper_and_shadow(monkeypatch):
    firebase = InMemoryFirebase()
    account_store = AccountStore()
    paper_ledger = PaperDecisionLedger(firebase=firebase)
    shadow_ledger = ShadowDecisionLedger(firebase=firebase)

    first = run_symbol(
        SimpleNamespace(history=lambda symbol, period="3mo": deterministic_b3_frame()),
        account_store,
        paper_ledger,
        "PETR4",
        execute=False,
        shadow_ledger=shadow_ledger,
    )
    second = run_symbol(
        SimpleNamespace(history=lambda symbol, period="3mo": deterministic_b3_frame()),
        account_store,
        paper_ledger,
        "PETR4",
        execute=False,
        shadow_ledger=shadow_ledger,
    )

    assert first.status == "decided"
    assert second.status == "duplicate_skipped"
    assert second.signal_id == first.signal_id
    assert second.shadow_id == first.shadow_id
    assert len(paper_ledger.list_records(symbol="PETR4")) == 1
    assert len(shadow_ledger.list_records(symbol="PETR4")) == 1
    assert account_store.account.orders == []
    assert account_store.save_calls == 0


def test_risk_rejection_blocks_demo_promotion(monkeypatch):
    def fake_evaluate(*args, **kwargs):
        return {
            "decision": {
                "action": "BUY",
                "quantity": 0,
                "reference_price": 61.0,
                "risk_allowed": False,
                "reason": "risk gate rejected",
            },
            "executed": False,
            "order": None,
        }

    monkeypatch.setattr("app.services.paper_scheduler.evaluate_paper_signal", fake_evaluate)

    result = run_symbol(
        SimpleNamespace(history=lambda symbol, period="3mo": deterministic_b3_frame()),
        AccountStore(),
        PaperDecisionLedger(firebase=InMemoryFirebase()),
        "PETR4",
        execute=False,
        demo_bridge=SchedulerDemoBridge(enabled=True, symbol_map={"PETR4": "PETR4"}),
    )

    assert result.status == "decided"
    assert result.risk_allowed is False
    assert result.demo_plan is not None
    assert result.demo_plan.status == "blocked"
    assert result.demo_plan.intent is None


def test_demo_bridge_requires_enablement_and_explicit_mapping():
    result = SimpleNamespace(
        symbol="PETR4",
        status="decided",
        signal_id="signal-1",
        action="BUY",
        quantity=2.0,
        reference_price=61.0,
        risk_allowed=True,
    )

    disabled = SchedulerDemoBridge().plan(result)
    unmapped = SchedulerDemoBridge(enabled=True).plan(result)
    ready = SchedulerDemoBridge(
        enabled=True, symbol_map={"PETR4": "PETR4"}
    ).plan(result)

    assert disabled.status == "disabled"
    assert disabled.intent is None
    assert unmapped.status == "blocked"
    assert unmapped.intent is None
    assert ready.status == "ready"
    assert ready.intent is not None
    assert ready.intent.symbol == "PETR4"
    assert "submission remains disabled" in ready.reason


def test_demo_ready_plan_never_submits_to_a_broker(monkeypatch):
    submission_calls: list[tuple] = []

    def forbidden_submit(*args, **kwargs):
        submission_calls.append((args, kwargs))
        raise AssertionError("broker submission must never be reached")

    monkeypatch.setattr(PaperAccount, "submit_order", forbidden_submit)

    def fake_evaluate(*args, **kwargs):
        assert kwargs["execute"] is False
        return {
            "decision": {
                "action": "BUY",
                "quantity": 2,
                "reference_price": 61.0,
                "risk_allowed": True,
                "reason": "deterministic BUY",
            },
            "executed": False,
            "order": None,
        }

    monkeypatch.setattr("app.services.paper_scheduler.evaluate_paper_signal", fake_evaluate)

    result = run_symbol(
        SimpleNamespace(history=lambda symbol, period="3mo": deterministic_b3_frame()),
        AccountStore(),
        PaperDecisionLedger(firebase=InMemoryFirebase()),
        "PETR4",
        execute=False,
        demo_bridge=SchedulerDemoBridge(enabled=True, symbol_map={"PETR4": "PETR4"}),
    )

    assert result.executed is False
    assert result.demo_plan is not None
    assert result.demo_plan.status == "ready"
    assert result.demo_plan.intent is not None
    assert submission_calls == []


def test_run_scheduler_converts_provider_failure_to_error_result():
    class FailingProvider:
        def history(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
            raise RuntimeError("provider unavailable")

    result = run_scheduler(
        ["PETR4"],
        provider=FailingProvider(),
        account_store=AccountStore(),
        ledger=PaperDecisionLedger(firebase=InMemoryFirebase()),
        execute=False,
        force=True,
    )

    assert len(result) == 1
    assert result[0].status == "error"
    assert result[0].symbol == "PETR4"
    assert "provider unavailable" in result[0].reason
