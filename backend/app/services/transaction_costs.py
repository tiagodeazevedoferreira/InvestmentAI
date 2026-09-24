from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import median


@dataclass(frozen=True)
class CostObservation:
    """One realized execution-cost observation used for descriptive calibration."""

    venue: str
    source: str
    notional: float
    commission: float
    expected_price: float
    executed_price: float
    quantity: float

    def __post_init__(self) -> None:
        if not self.venue.strip():
            raise ValueError("venue cannot be empty")
        if not self.source.strip():
            raise ValueError("source cannot be empty")
        for name in (
            "notional",
            "commission",
            "expected_price",
            "executed_price",
            "quantity",
        ):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.notional <= 0:
            raise ValueError("notional must be positive")
        if self.commission < 0:
            raise ValueError("commission cannot be negative")
        if self.expected_price <= 0 or self.executed_price <= 0:
            raise ValueError("prices must be positive")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


@dataclass(frozen=True)
class VenueCostCalibration:
    """Immutable descriptive cost profile; never authorizes execution."""

    venue: str
    source: str
    observations: int
    median_commission_bps: float
    p95_commission_bps: float
    median_slippage_bps: float
    p95_slippage_bps: float


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def calibrate_venue_costs(observations: list[CostObservation]) -> VenueCostCalibration:
    """Calibrate descriptive commission/slippage statistics from realized observations."""
    if not observations:
        raise ValueError("observations cannot be empty")

    venues = {item.venue.strip().upper() for item in observations}
    sources = {item.source.strip() for item in observations}
    if len(venues) != 1:
        raise ValueError("all observations must use the same venue")
    if len(sources) != 1:
        raise ValueError("all observations must use the same source")

    commission_bps = [
        float(item.commission) / float(item.notional) * 10_000.0
        for item in observations
    ]
    slippage_bps = [
        abs(float(item.executed_price) - float(item.expected_price))
        / float(item.expected_price)
        * 10_000.0
        for item in observations
    ]

    for values, name in (
        (commission_bps, "commission"),
        (slippage_bps, "slippage"),
    ):
        if not all(isfinite(value) and value >= 0 for value in values):
            raise ValueError(f"{name} basis points must be finite and non-negative")

    return VenueCostCalibration(
        venue=next(iter(venues)),
        source=next(iter(sources)),
        observations=len(observations),
        median_commission_bps=float(median(commission_bps)),
        p95_commission_bps=float(_percentile(commission_bps, 0.95)),
        median_slippage_bps=float(median(slippage_bps)),
        p95_slippage_bps=float(_percentile(slippage_bps, 0.95)),
    )
