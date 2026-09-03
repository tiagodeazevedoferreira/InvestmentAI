import pandas as pd
import pytest

from backend.app.services.paper_outcomes import attribute_decision, summarize_outcomes


def bars(values):
    return pd.DataFrame(
        {"Close": [float(value) for value in values]},
        index=pd.date_range("2026-09-01", periods=len(values), freq="D", tz="UTC"),
    )


def decision(action="BUY"):
    return {
        "signal_id": "abc123",
        "symbol": "PETR4",
        "action": action,
        "bar_timestamp": "2026-09-01T00:00:00+00:00",
        "price": 100.0,
    }


def test_buy_outcome_uses_forward_return_and_hit():
    observations = attribute_decision(decision("BUY"), bars([100, 101, 103, 104, 105, 106]))
    one_day = next(item for item in observations if item.horizon_bars == 1)
    assert one_day.outcome_price == 101.0
    assert one_day.forward_return == pytest.approx(0.01)
    assert one_day.signed_return == pytest.approx(0.01)
    assert one_day.hit is True


def test_sell_outcome_inverts_return_for_hit_rate():
    observations = attribute_decision(decision("SELL"), bars([100, 99, 97, 96, 95, 94]))
    one_day = next(item for item in observations if item.horizon_bars == 1)
    assert one_day.forward_return == pytest.approx(-0.01)
    assert one_day.signed_return == pytest.approx(0.01)
    assert one_day.hit is True


def test_incomplete_horizon_is_explicitly_pending():
    observations = attribute_decision(decision(), bars([100, 101, 102]), horizons=(1, 5))
    long_horizon = next(item for item in observations if item.horizon_bars == 5)
    assert long_horizon.outcome_price is None
    assert long_horizon.signed_return is None
    assert long_horizon.hit is None


def test_hold_has_no_hit_classification():
    observations = attribute_decision(decision("HOLD"), bars([100, 101, 99, 102]), horizons=(1,))
    assert observations[0].hit is None
    assert observations[0].signed_return == pytest.approx(0.01)


def test_unknown_decision_timestamp_is_rejected():
    bad = {**decision(), "bar_timestamp": "2026-08-31T00:00:00+00:00"}
    with pytest.raises(ValueError, match="timestamp not found"):
        attribute_decision(bad, bars([100, 101, 102]))


def test_summary_aggregates_hit_rate_and_mean_signed_return():
    buy = attribute_decision(decision("BUY"), bars([100, 101, 99, 103]), horizons=(1,))
    sell = attribute_decision(decision("SELL"), bars([100, 99, 98, 97]), horizons=(1,))
    summary = summarize_outcomes(buy + sell)
    assert summary["observations"] == 2
    groups = {f"{item['action']}:{item['horizon_bars']}": item for item in summary["groups"]}
    assert groups["BUY:1"]["hit_rate"] == pytest.approx(1.0)
    assert groups["SELL:1"]["hit_rate"] == pytest.approx(1.0)
