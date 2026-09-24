from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class ProviderOutcomeObservation:
    provider: str
    symbol: str
    horizon_bars: int
    confidence: float
    hit: bool
    signed_return: float
    timestamp: str

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider is required")
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.horizon_bars <= 0:
            raise ValueError("horizon_bars must be positive")
        if not 0.0 <= self.confidence <= 1.0 or not isfinite(self.confidence):
            raise ValueError("confidence must be finite and between 0 and 1")
        if not isfinite(self.signed_return):
            raise ValueError("signed_return must be finite")
        if not self.timestamp.strip():
            raise ValueError("timestamp is required")


@dataclass(frozen=True)
class ProviderCalibrationGroup:
    provider: str
    horizon_bars: int
    observations: int
    hits: int
    hit_rate: float
    mean_confidence: float
    brier_score: float
    calibration_gap: float
    mean_signed_return: float


def build_provider_calibration(
    observations: Iterable[ProviderOutcomeObservation],
) -> dict:
    """Build deterministic, descriptive provider-vs-outcome calibration statistics.

    The report is observational only: it never changes weights, thresholds,
    risk gates or execution authorization.
    """
    items = list(observations)
    if not items:
        raise ValueError("at least one observation is required")

    grouped: dict[tuple[str, int], list[ProviderOutcomeObservation]] = {}
    for item in items:
        grouped.setdefault((item.provider.strip().lower(), item.horizon_bars), []).append(item)

    groups: list[ProviderCalibrationGroup] = []
    for (provider, horizon), bucket in sorted(grouped.items()):
        n = len(bucket)
        hits = sum(1 for item in bucket if item.hit)
        hit_rate = hits / n
        mean_confidence = sum(item.confidence for item in bucket) / n
        brier = sum((item.confidence - (1.0 if item.hit else 0.0)) ** 2 for item in bucket) / n
        mean_return = sum(item.signed_return for item in bucket) / n
        groups.append(
            ProviderCalibrationGroup(
                provider=provider,
                horizon_bars=horizon,
                observations=n,
                hits=hits,
                hit_rate=hit_rate,
                mean_confidence=mean_confidence,
                brier_score=brier,
                calibration_gap=mean_confidence - hit_rate,
                mean_signed_return=mean_return,
            )
        )

    return {
        "method": "provider_outcome_calibration_v1",
        "observations": len(items),
        "providers": sorted({item.provider.strip().lower() for item in items}),
        "groups": [group.__dict__ for group in groups],
        "interpretation": {
            "promotion_allowed": False,
            "weights_or_thresholds_changed": False,
            "execution_authority": False,
        },
    }
