import math

import pytest

from app.services.fundamental_scoring import (
    FundamentalScoreConfig,
    MetricRule,
    DEFAULT_FUNDAMENTAL_SCORE_CONFIG,
    fundamental_score,
    margin_of_safety,
    rank_fundamentals,
)


def full_metrics(**overrides):
    metrics = {
        "pe": 15.0,
        "pb": 2.0,
        "ev_ebitda": 10.0,
        "roe": 0.15,
        "roic": 0.12,
        "dividend_yield": 0.04,
    }
    metrics.update(overrides)
    return metrics


def test_default_config_weights_sum_to_one():
    assert sum(rule.weight for rule in DEFAULT_FUNDAMENTAL_SCORE_CONFIG.rules.values()) == pytest.approx(1.0)


def test_component_scores_use_direction_and_clamp_to_zero_one():
    result = fundamental_score(
        full_metrics(
            pe=5.0,
            pb=4.0,
            ev_ebitda=18.0,
            roe=0.25,
            roic=0.05,
            dividend_yield=0.08,
        )
    )
    assert result["component_scores"]["pe"] == pytest.approx(1.0)
    assert result["component_scores"]["pb"] == pytest.approx(0.0)
    assert result["component_scores"]["ev_ebitda"] == pytest.approx(0.0)
    assert result["component_scores"]["roe"] == pytest.approx(1.0)
    assert result["component_scores"]["roic"] == pytest.approx(0.0)
    assert result["component_scores"]["dividend_yield"] == pytest.approx(1.0)
    assert 0.0 <= result["score"] <= 1.0


def test_values_outside_bounds_are_clamped():
    result = fundamental_score(full_metrics(pe=100.0, roe=-1.0))
    assert result["component_scores"]["pe"] == 0.0
    assert result["component_scores"]["roe"] == 0.0

    result = fundamental_score(full_metrics(pe=0.0, roe=2.0))
    assert result["component_scores"]["pe"] == 1.0
    assert result["component_scores"]["roe"] == 1.0


def test_missing_required_metric_fails_closed():
    metrics = full_metrics()
    del metrics["roic"]
    with pytest.raises(ValueError, match="missing required metrics"):
        fundamental_score(metrics)


def test_invalid_metric_configuration_fails_closed():
    with pytest.raises(ValueError, match="weights must sum to 1"):
        FundamentalScoreConfig(
            rules={
                "pe": MetricRule(0.5, 5.0, 25.0, False),
                "roe": MetricRule(0.4, 0.05, 0.25, True),
            }
        )


def test_non_finite_metric_fails_closed():
    with pytest.raises(ValueError, match="metric value must be finite"):
        fundamental_score(full_metrics(pe=math.inf))


def test_ranking_is_deterministic_and_tie_breaks_by_symbol():
    snapshots = [
        {"symbol": "vale3", "metrics": full_metrics()},
        {"symbol": "PETR4", "metrics": full_metrics()},
    ]
    ranked = rank_fundamentals(snapshots)
    assert [item["symbol"] for item in ranked] == ["PETR4", "VALE3"]


def test_ranking_orders_by_score_descending():
    snapshots = [
        {"symbol": "AAA", "metrics": full_metrics(pe=24.0, roe=0.06)},
        {"symbol": "BBB", "metrics": full_metrics(pe=6.0, roe=0.24)},
    ]
    ranked = rank_fundamentals(snapshots)
    assert ranked[0]["symbol"] == "BBB"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_margin_of_safety():
    assert margin_of_safety(80.0, 100.0) == pytest.approx(0.20)
    assert margin_of_safety(120.0, 100.0) == pytest.approx(-0.20)


@pytest.mark.parametrize(
    "market_price,intrinsic_value",
    [
        (math.inf, 100.0),
        (100.0, math.inf),
        (100.0, 0.0),
        (100.0, -1.0),
    ],
)
def test_margin_of_safety_rejects_invalid_inputs(market_price, intrinsic_value):
    with pytest.raises(ValueError):
        margin_of_safety(market_price, intrinsic_value)
