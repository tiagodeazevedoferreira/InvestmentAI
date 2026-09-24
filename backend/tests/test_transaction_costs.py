from __future__ import annotations

import math

import pytest

from app.services.transaction_costs import (
    CostObservation,
    calibrate_venue_costs,
)


def test_calibration_is_deterministic_and_reports_median_p95():
    observations = [
        CostObservation(
            venue="B3",
            source="synthetic",
            notional=100_000.0,
            commission=100.0,
            expected_price=100.0,
            executed_price=100.05,
            quantity=1000.0,
        ),
        CostObservation(
            venue="B3",
            source="synthetic",
            notional=80_000.0,
            commission=80.0,
            expected_price=100.0,
            executed_price=100.02,
            quantity=800.0,
        ),
        CostObservation(
            venue="B3",
            source="synthetic",
            notional=120_000.0,
            commission=180.0,
            expected_price=100.0,
            executed_price=100.10,
            quantity=1200.0,
        ),
    ]

    first = calibrate_venue_costs(observations)
    second = calibrate_venue_costs(observations)

    assert first == second
    assert first.venue == "B3"
    assert first.observations == 3
    assert first.median_commission_bps == pytest.approx(10.0)
    assert first.p95_commission_bps == pytest.approx(14.5)
    assert first.median_slippage_bps == pytest.approx(5.0)
    assert first.p95_slippage_bps == pytest.approx(9.5)
    assert first.source == "synthetic"


def test_calibration_requires_one_venue_and_preserves_source():
    observations = [
        CostObservation(
            venue="B3",
            source="fixture-v1",
            notional=10_000.0,
            commission=10.0,
            expected_price=100.0,
            executed_price=100.01,
            quantity=100.0,
        ),
        CostObservation(
            venue="B3",
            source="fixture-v1",
            notional=20_000.0,
            commission=20.0,
            expected_price=100.0,
            executed_price=99.99,
            quantity=200.0,
        ),
    ]

    profile = calibrate_venue_costs(observations)

    assert profile.venue == "B3"
    assert profile.source == "fixture-v1"
    assert profile.observations == 2
    assert profile.median_slippage_bps == pytest.approx(1.0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("notional", 0.0),
        ("commission", -1.0),
        ("expected_price", 0.0),
        ("executed_price", math.nan),
        ("quantity", -1.0),
    ],
)
def test_invalid_cost_observation_fails_closed(field, value):
    values = {
        "venue": "B3",
        "source": "synthetic",
        "notional": 100.0,
        "commission": 1.0,
        "expected_price": 100.0,
        "executed_price": 100.01,
        "quantity": 1.0,
    }
    values[field] = value

    with pytest.raises(ValueError):
        calibrate_venue_costs([CostObservation(**values)])


def test_calibration_rejects_mixed_venues_and_sources():
    base = dict(
        notional=10_000.0,
        commission=10.0,
        expected_price=100.0,
        executed_price=100.01,
        quantity=100.0,
    )

    with pytest.raises(ValueError, match="same venue"):
        calibrate_venue_costs([
            CostObservation(venue="B3", source="synthetic", **base),
            CostObservation(venue="NYSE", source="synthetic", **base),
        ])

    with pytest.raises(ValueError, match="same source"):
        calibrate_venue_costs([
            CostObservation(venue="B3", source="synthetic-a", **base),
            CostObservation(venue="B3", source="synthetic-b", **base),
        ])
