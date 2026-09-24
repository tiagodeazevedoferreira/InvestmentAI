from __future__ import annotations

import pandas as pd
import pytest

from backend.app.services.paper_calibration_runner import calibrate_persisted_paper_outcomes


class FakeProvider:
    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.calls: list[tuple[str, str]] = []

    def history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        self.calls.append((symbol, period))
        return self.frame


class FakeLedger:
    def __init__(self, records: list[dict]):
        self.records = records
        self.saved: dict[str, list] = {}

    def list_records(self, *, symbol=None, limit=200):
        records = self.records if symbol is None else [r for r in self.records if r["symbol"] == symbol]
        return records[:limit]

    def save_outcomes(self, signal_id: str, observations: list) -> dict:
        self.saved[signal_id] = observations
        return self.records[0]


def test_runner_persists_completed_and_incomplete_horizons():
    index = pd.date_range("2026-09-01", periods=3, freq="D", tz="UTC")
    frame = pd.DataFrame({"Close": [100.0, 102.0, 101.0]}, index=index)
    record = {
        "signal_id": "abc",
        "symbol": "PETR4",
        "bar_timestamp": index[0].isoformat(),
        "action": "BUY",
        "decision_price": 100.0,
    }
    ledger = FakeLedger([record])
    provider = FakeProvider(frame)

    result = calibrate_persisted_paper_outcomes(
        ledger,
        provider,
        horizons=(1, 5),
        transaction_cost_bps=5.0,
    )

    assert result.decisions_seen == 1
    assert result.decisions_processed == 1
    assert result.outcomes_persisted == 2
    assert result.completed_observations == 1
    assert result.incomplete_observations == 1
    assert result.report["observations"] == 1
    assert result.report["groups"][0]["action"] == "BUY"
    assert ledger.saved["abc"][0].signed_return == pytest.approx(0.02)
    assert ledger.saved["abc"][1].signed_return is None


def test_runner_rejects_missing_causal_price():
    index = pd.date_range("2026-09-01", periods=2, freq="D", tz="UTC")
    frame = pd.DataFrame({"Close": [100.0, 101.0]}, index=index)
    ledger = FakeLedger([{
        "signal_id": "abc", "symbol": "PETR4",
        "bar_timestamp": index[0].isoformat(), "action": "BUY",
    }])

    with pytest.raises(ValueError, match="causal decision provenance"):
        calibrate_persisted_paper_outcomes(ledger, FakeProvider(frame), horizons=(1,))


def test_runner_is_bounded_to_requested_symbol_and_limit():
    index = pd.date_range("2026-09-01", periods=2, freq="D", tz="UTC")
    frame = pd.DataFrame({"Close": [100.0, 101.0]}, index=index)
    records = [{
        "signal_id": f"{i}", "symbol": "PETR4", "bar_timestamp": index[0].isoformat(),
        "action": "BUY", "decision_price": 100.0,
    } for i in range(3)]
    ledger = FakeLedger(records)
    provider = FakeProvider(frame)

    result = calibrate_persisted_paper_outcomes(ledger, provider, symbol="PETR4", limit=2, horizons=(1,))

    assert result.decisions_seen == 2
    assert len(provider.calls) == 2
    assert set(ledger.saved) == {"0", "1"}
