from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence


_METRICS = ("pe", "pb", "ev_ebitda", "roe", "roic", "dividend_yield")


@dataclass(frozen=True)
class MetricRule:
    weight: float
    lower: float
    upper: float
    higher_is_better: bool

    def __post_init__(self) -> None:
        values = (self.weight, self.lower, self.upper)
        if any(not math.isfinite(float(value)) for value in values):
            raise ValueError("metric rule values must be finite")
        if self.weight < 0:
            raise ValueError("metric weight must be non-negative")
        if self.lower >= self.upper:
            raise ValueError("metric lower bound must be less than upper bound")


@dataclass(frozen=True)
class FundamentalScoreConfig:
    rules: Mapping[str, MetricRule]

    def __post_init__(self) -> None:
        if not self.rules:
            raise ValueError("at least one metric rule is required")
        unknown = set(self.rules) - set(_METRICS)
        if unknown:
            raise ValueError(f"unsupported metrics: {sorted(unknown)}")
        if any(rule.weight <= 0 for rule in self.rules.values()):
            raise ValueError("configured metric weights must be greater than zero")
        weight_sum = sum(rule.weight for rule in self.rules.values())
        if not math.isclose(weight_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("metric weights must sum to 1")


DEFAULT_FUNDAMENTAL_SCORE_CONFIG = FundamentalScoreConfig(
    rules={
        "pe": MetricRule(1 / 6, 5.0, 25.0, False),
        "pb": MetricRule(1 / 6, 0.5, 4.0, False),
        "ev_ebitda": MetricRule(1 / 6, 4.0, 18.0, False),
        "roe": MetricRule(1 / 6, 0.05, 0.25, True),
        "roic": MetricRule(1 / 6, 0.05, 0.20, True),
        "dividend_yield": MetricRule(1 / 6, 0.01, 0.08, True),
    }
)


def _validate_finite(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _component_score(value: float, rule: MetricRule) -> float:
    value = _validate_finite(value, "metric value")
    span = rule.upper - rule.lower
    if rule.higher_is_better:
        raw = (value - rule.lower) / span
    else:
        raw = (rule.upper - value) / span
    return min(1.0, max(0.0, raw))


def fundamental_score(
    metrics: Mapping[str, float],
    config: FundamentalScoreConfig = DEFAULT_FUNDAMENTAL_SCORE_CONFIG,
) -> dict:
    """Return deterministic component and aggregate fundamental scores.

    All metrics configured in config are required. Missing values fail closed
    rather than being imputed or silently reweighted.
    """
    missing = [name for name in config.rules if name not in metrics or metrics[name] is None]
    if missing:
        raise ValueError(f"missing required metrics: {sorted(missing)}")

    component_scores = {
        name: _component_score(metrics[name], rule)
        for name, rule in config.rules.items()
    }
    contributions = {
        name: component_scores[name] * config.rules[name].weight
        for name in config.rules
    }
    score = sum(contributions.values())
    return {
        "score": score,
        "component_scores": component_scores,
        "weighted_contributions": contributions,
    }


def rank_fundamentals(
    snapshots: Sequence[Mapping[str, object]],
    config: FundamentalScoreConfig = DEFAULT_FUNDAMENTAL_SCORE_CONFIG,
) -> list[dict]:
    """Score and rank fundamental snapshots deterministically.

    Each snapshot must contain a non-empty symbol and a metrics mapping.
    Ties are resolved by normalized symbol in ascending lexical order.
    """
    ranked = []
    for snapshot in snapshots:
        symbol = str(snapshot.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("snapshot symbol is required")
        metrics = snapshot.get("metrics")
        if not isinstance(metrics, Mapping):
            raise ValueError("snapshot metrics must be a mapping")
        result = fundamental_score(metrics, config)
        ranked.append(
            {
                "symbol": symbol,
                "score": result["score"],
                "component_scores": result["component_scores"],
                "weighted_contributions": result["weighted_contributions"],
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["symbol"]))
    return ranked


def margin_of_safety(market_price: float, intrinsic_value: float) -> float:
    """Return (intrinsic value - market price) / intrinsic value."""
    market_price = _validate_finite(market_price, "market price")
    intrinsic_value = _validate_finite(intrinsic_value, "intrinsic value")
    if intrinsic_value <= 0:
        raise ValueError("intrinsic value must be greater than zero")
    return (intrinsic_value - market_price) / intrinsic_value
