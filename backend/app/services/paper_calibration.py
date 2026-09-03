from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import NormalDist
from typing import Iterable

from scipy.stats import t

from .paper_outcomes import OutcomeObservation


@dataclass(frozen=True)
class CalibrationGroup:
    action: str
    horizon_bars: int
    observations: int
    hits: int
    hit_rate: float | None
    hit_rate_ci95: tuple[float | None, float | None]
    mean_gross_signed_return: float | None
    mean_net_signed_return: float | None
    median_net_signed_return: float | None
    mean_ci95: tuple[float | None, float | None]


def _wilson_interval(hits: int, observations: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if observations <= 0:
        return None, None
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
    standard_error = sqrt(variance / n)
    critical = float(t.ppf(0.975, n - 1))
    margin = critical * standard_error
    return mean - margin, mean + margin


def build_calibration_report(
    observations: Iterable[OutcomeObservation],
    *,
    transaction_cost_bps: float = 0.0,
) -> dict:
    """Build descriptive calibration statistics from completed paper outcomes.

    ``transaction_cost_bps`` is a round-trip cost assumption applied once to
    each signed forward return. It is deliberately an explicit assumption,
    not a venue-calibrated estimate.
    """
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be non-negative")
    grouped: dict[tuple[str, int], list[OutcomeObservation]] = {}
    for item in observations:
        if item.signed_return is None:
            continue
        grouped.setdefault((item.action, item.horizon_bars), []).append(item)

    groups: list[CalibrationGroup] = []
    cost = transaction_cost_bps / 10_000.0
    for (action, horizon), items in sorted(grouped.items()):
        gross = [float(item.signed_return) for item in items]
        net = [value - cost for value in gross]
        hits = sum(1 for item in items if item.hit is True)
        mean_gross = sum(gross) / len(gross)
        mean_net = sum(net) / len(net)
        median_net = sorted(net)[len(net) // 2] if len(net) % 2 else (sorted(net)[len(net) // 2 - 1] + sorted(net)[len(net) // 2]) / 2.0
        groups.append(
            CalibrationGroup(
                action=action,
                horizon_bars=horizon,
                observations=len(items),
                hits=hits,
                hit_rate=hits / len(items),
                hit_rate_ci95=_wilson_interval(hits, len(items)),
                mean_gross_signed_return=mean_gross,
                mean_net_signed_return=mean_net,
                median_net_signed_return=median_net,
                mean_ci95=_mean_interval(gross),
            )
        )

    return {
        "method": "descriptive_paper_calibration_v1",
        "transaction_cost_bps_round_trip": transaction_cost_bps,
        "observations": sum(group.observations for group in groups),
        "groups": [group.__dict__ for group in groups],
        "interpretation": {
            "promotion_allowed": False,
            "note": "Descriptive paper outcomes do not authorize model or policy promotion.",
        },
    }
