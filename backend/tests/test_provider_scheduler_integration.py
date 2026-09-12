from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pandas as pd

from app.services.paper_execution import PaperAccount
from app.services.paper_ledger import PaperDecisionLedger
from app.services.paper_scheduler import run_symbol
from app.services.providers import OpenBBProvider, get_provider
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


def test_openbb_provider_factory_feeds_scheduler_without_external_network(monkeypatch):
    frame = deterministic_b3_frame()
    calls: list[tuple[str, str]] = []

    def fake_history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        calls.append((symbol, period))
        return frame.copy()

    monkeypatch.setattr(OpenBBProvider, "history", fake_history)

    provider = get_provider("openbb")
    firebase = InMemoryFirebase()
    account_store = AccountStore()
    paper_ledger = PaperDecisionLedger(firebase=firebase)
    shadow_ledger = ShadowDecisionLedger(firebase=firebase)

    result = run_symbol(
        provider,
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
    assert paper_ledger.get(result.signal_id)["status"] == "completed"
    assert shadow_ledger.get(result.shadow_id)["execution_authority"] == "none"
