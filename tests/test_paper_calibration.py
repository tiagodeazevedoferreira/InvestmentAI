import pytest

from backend.app.services.paper_calibration import build_calibration_report
from backend.app.services.paper_outcomes import OutcomeObservation


def make_observation(signal_id, action, signed_return, hit, horizon=1):
    return OutcomeObservation(signal_id, "TEST", action, "2026-09-01T00:00:00+00:00", 100.0, horizon, "2026-09-02T00:00:00+00:00", 100.0, signed_return, signed_return, hit)


def test_explicit_cost_is_subtracted():
    report = build_calibration_report([
        make_observation("a", "BUY", 0.01, True),
        make_observation("b", "BUY", -0.005, False),
    ], transaction_cost_bps=10)
    group = report["groups"][0]
    assert group["observations"] == 2
    assert group["hit_rate"] == pytest.approx(0.5)
    assert group["mean_gross_signed_return"] == pytest.approx(0.0025)
    assert group["mean_net_signed_return"] == pytest.approx(0.0015)
    assert group["hit_rate_ci95"][0] < 0.5 < group["hit_rate_ci95"][1]


def test_regime_partition_is_supported():
    report = build_calibration_report([
        make_observation("low", "SELL", 0.02, True),
        make_observation("high", "SELL", -0.01, False),
    ], regime_by_signal={"low": "low_vol", "high": "high_vol"})
    assert {item["regime"] for item in report["groups"]} == {"low_vol", "high_vol"}


def test_promotion_is_never_authorized():
    report = build_calibration_report([make_observation("a", "BUY", 0.01, True)])
    assert report["interpretation"]["promotion_allowed"] is False
