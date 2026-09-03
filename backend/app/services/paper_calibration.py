from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Mapping

from scipy.stats import t

from .paper_outcomes import OutcomeObservation


@dataclass(frozen=True)
class CalibrationGroup:
    action: str
    horizon_bars: int
    regime: str
    observations: int
    hits: int
    hit_rate: float | None
    hit_rate_ci95: tuple[float | None, float | None]
    mean_gross_signed_return: float | None
    mean_net_signed_return: float | None
    median_net_signed_return: float | None
    mean_ci95: tuple[float | None, float | None]


def _wilson_interval(hits: int, observations: int) -> tuple[float | None, float | None]:
    if observations <= 0:
        return None, None
    z = 1.959963984540054
    p = hits / observations
    denominator = 1.0 + z * z / observations
    centre = (p + z * z / (2.0 * observations)) / denominator
    margin = z * sqrt((p * (1.0 - p) + z * z / (4.0 * observations)) / observations) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _mean_interval(values: list[float]) -> tuple[float | None, float | None]:
    n = len(values)
    if n == 0:
        return None, None
    mean = sum(values) / n
    if n == 1:
        return mean, mean
    variance = sum((value - mean) ** 2 for value in values) / (n - 1)
    margin = float(t.ppf(0.975, n - 1)) * sqrt(variance / n)
    return mean - margin, mean + margin


def build_calibration_report(observations: Iterable[OutcomeObservation], *, transaction_cost_bps: float = 0.0, regime_by_signal: Mapping[str, str] | None = None) -> dict:
    """Build descriptive calibration statistics; never authorizes promotion."""
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be non-negative")
    regimes = regime_by_signal or {}
    grouped: dict[tuple[str, int, str], list[OutcomeObservation]] = {}
    for item in observations:
        if item.signed_return is not None:
            grouped.setdefault((item.action, item.horizon_bars, str(regimes.get(item.signal_id, "all"))), []).append(item)

    groups: list[CalibrationGroup] = []
    cost = transaction_cost_bps / 10_000.0
    for (action, horizon, regime), items in sorted(grouped.items()):
        gross = [float(item.signed_return) for item in items]
        net = [value - cost for value in gross]
        ordered = sorted(net)
        middle = len(ordered) // 2
        median_net = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
        hits = sum(1 for item in items if item.hit is True)
        groups.append(CalibrationGroup(action, horizon, regime, len(items), hits, hits / len(items), _wilson_interval(hits, len(items)), sum(gross) / len(gross), sum(net) / len(net), median_net, _mean_interval(gross)))

    return {
        "method": "descriptive_paper_calibration_v1",
        "transaction_cost_bps_round_trip": transaction_cost_bps,
        "observations": sum(group.observations for group in groups),
        "groups": [group.__dict__ for group in groups],
        "interpretation": {"promotion_allowed": False, "note": "Descriptive paper outcomes do not authorize model or policy promotion."},
    }
