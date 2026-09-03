from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PromotionCriteria:
    min_observations: int = 30
    min_hit_rate_ci95_lower: float = 0.50
    min_mean_net_return: float = 0.0
    max_regime_hit_rate_degradation: float = 0.10
    max_tv_conflict_rate: float = 0.10


def _groups(report: Mapping[str, Any], action: str, horizon_bars: int) -> list[Mapping[str, Any]]:
    return [
        group
        for group in report.get("groups", [])
        if group.get("action") == action and int(group.get("horizon_bars", -1)) == horizon_bars
    ]


def evaluate_promotion_gate(
    report: Mapping[str, Any],
    *,
    action: str = "BUY",
    horizon_bars: int = 5,
    criteria: PromotionCriteria | None = None,
    reconciliation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate predefined empirical evidence without changing trading policy.

    A passing result means the evidence is eligible for human review only. It
    never authorizes model, signal, risk, sizing, broker, or live promotion.
    """
    c = criteria or PromotionCriteria()
    if c.min_observations <= 0:
        raise ValueError("min_observations must be positive")
    if not 0.0 <= c.min_hit_rate_ci95_lower <= 1.0:
        raise ValueError("min_hit_rate_ci95_lower must be between 0 and 1")
    if c.min_mean_net_return < 0.0:
        raise ValueError("min_mean_net_return must be non-negative")
    if not 0.0 <= c.max_regime_hit_rate_degradation <= 1.0:
        raise ValueError("max_regime_hit_rate_degradation must be between 0 and 1")
    if not 0.0 <= c.max_tv_conflict_rate <= 1.0:
        raise ValueError("max_tv_conflict_rate must be between 0 and 1")

    reasons: list[str] = []
    base = [g for g in _groups(report, action, horizon_bars) if g.get("regime") == "all"]
    if len(base) != 1:
        reasons.append("missing_or_ambiguous_all_regime_group")
    else:
        group = base[0]
        observations = int(group.get("observations", 0))
        ci = group.get("hit_rate_ci95") or [None, None]
        lower = ci[0] if len(ci) else None
        mean_net = group.get("mean_net_signed_return")
        if observations < c.min_observations:
            reasons.append("insufficient_observations")
        if lower is None or float(lower) < c.min_hit_rate_ci95_lower:
            reasons.append("hit_rate_confidence_bound_below_threshold")
        if mean_net is None or float(mean_net) < c.min_mean_net_return:
            reasons.append("mean_net_return_below_threshold")

    regime_groups = [g for g in _groups(report, action, horizon_bars) if g.get("regime") not in (None, "all", "insufficient_history")]
    if base and regime_groups:
        base_hit = base[0].get("hit_rate")
        if base_hit is not None:
            for group in regime_groups:
                hit = group.get("hit_rate")
                if hit is not None and float(base_hit) - float(hit) > c.max_regime_hit_rate_degradation:
                    reasons.append(f"regime_degradation:{group.get('regime')}")

    reconciliation_summary = reconciliation or {}
    conflict_rate = reconciliation_summary.get("conflict_rate")
    if conflict_rate is not None and float(conflict_rate) > c.max_tv_conflict_rate:
        reasons.append("tradingview_conflict_rate_above_threshold")

    evidence_passed = not reasons
    return {
        "method": "empirical_paper_promotion_gate_v1",
        "scope": {"action": action, "horizon_bars": horizon_bars},
        "criteria": {
            "min_observations": c.min_observations,
            "min_hit_rate_ci95_lower": c.min_hit_rate_ci95_lower,
            "min_mean_net_return": c.min_mean_net_return,
            "max_regime_hit_rate_degradation": c.max_regime_hit_rate_degradation,
            "max_tv_conflict_rate": c.max_tv_conflict_rate,
        },
        "evidence_passed": evidence_passed,
        "reasons": reasons,
        "promotion_allowed": False,
        "human_review_required": True,
        "execution_mode": "paper",
    }
