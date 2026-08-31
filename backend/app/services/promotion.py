from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionPolicy:
    min_sharpe: float = 1.0
    max_drawdown: float = -0.20
    min_samples: int = 100
    min_directional_accuracy: float = 0.52


def evaluate_promotion(metrics: dict, policy: PromotionPolicy | None = None) -> tuple[bool, list[str]]:
    p = policy or PromotionPolicy()
    failures = []
    if metrics.get("samples", 0) < p.min_samples:
        failures.append("insufficient_out_of_sample_samples")
    if metrics.get("directional_accuracy", 0) < p.min_directional_accuracy:
        failures.append("directional_accuracy_below_threshold")
    if metrics.get("sharpe", float("-inf")) < p.min_sharpe:
        failures.append("sharpe_below_threshold")
    if metrics.get("max_drawdown", 0) < p.max_drawdown:
        failures.append("drawdown_exceeds_limit")
    return not failures, failures
