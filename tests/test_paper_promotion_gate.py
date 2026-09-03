from app.services.paper_promotion_gate import PromotionCriteria, evaluate_promotion_gate


def group(*, regime="all", observations=40, hit_rate=0.65, lower=0.54, mean_net=0.002):
    return {
        "action": "BUY",
        "horizon_bars": 5,
        "regime": regime,
        "observations": observations,
        "hits": round(observations * hit_rate),
        "hit_rate": hit_rate,
        "hit_rate_ci95": [lower, 0.75],
        "mean_net_signed_return": mean_net,
    }


def test_gate_passes_evidence_but_never_allows_promotion():
    report = {"groups": [group()]}
    result = evaluate_promotion_gate(report)
    assert result["evidence_passed"] is True
    assert result["promotion_allowed"] is False
    assert result["human_review_required"] is True


def test_gate_rejects_insufficient_sample_and_weak_confidence_bound():
    report = {"groups": [group(observations=12, lower=0.40)]}
    result = evaluate_promotion_gate(report)
    assert result["evidence_passed"] is False
    assert "insufficient_observations" in result["reasons"]
    assert "hit_rate_confidence_bound_below_threshold" in result["reasons"]


def test_gate_rejects_negative_net_return():
    report = {"groups": [group(mean_net=-0.001)]}
    result = evaluate_promotion_gate(report)
    assert result["evidence_passed"] is False
    assert "mean_net_return_below_threshold" in result["reasons"]


def test_gate_checks_regime_degradation():
    report = {"groups": [group(), group(regime="high", hit_rate=0.40, lower=0.25)]}
    result = evaluate_promotion_gate(report)
    assert result["evidence_passed"] is False
    assert "regime_degradation:high" in result["reasons"]


def test_gate_checks_tradingview_conflict_rate():
    report = {"groups": [group()]}
    result = evaluate_promotion_gate(report, reconciliation={"conflict_rate": 0.25})
    assert result["evidence_passed"] is False
    assert "tradingview_conflict_rate_above_threshold" in result["reasons"]


def test_gate_is_strict_about_criteria_values():
    try:
        evaluate_promotion_gate({}, criteria=PromotionCriteria(min_observations=0))
    except ValueError as exc:
        assert "min_observations" in str(exc)
    else:
        raise AssertionError("invalid criteria should fail")
