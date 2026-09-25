import numpy as np
import pandas as pd
import pytest

from app.services.portfolio_risk_limits import (
    PortfolioRiskLimits,
    evaluate_portfolio_risk_limits,
)


def covariance(columns, diagonal):
    return pd.DataFrame(np.diag(diagonal), index=columns, columns=columns)


def test_passes_when_all_limits_are_within_bounds():
    columns = pd.Index(["PETR4", "VALE3"])
    limits = PortfolioRiskLimits(
        max_position_weight=0.70,
        max_gross_exposure=1.0,
        max_abs_net_exposure=1.0,
        max_annualized_volatility=0.30,
        max_daily_var_fraction=0.05,
    )
    result = evaluate_portfolio_risk_limits(
        [0.60, 0.40],
        covariance(columns, [0.0001, 0.0001]),
        limits,
        covariance_daily=covariance(columns, [0.0001 / 252, 0.0001 / 252]),
        portfolio_value=100_000,
    )
    assert result["approved"] is True
    assert result["breaches"] == []
    assert result["gross_exposure"] == pytest.approx(1.0)
    assert result["net_exposure"] == pytest.approx(1.0)


def test_reports_each_breached_limit_without_resizing():
    columns = pd.Index(["A", "B"])
    limits = PortfolioRiskLimits(
        max_position_weight=0.40,
        max_gross_exposure=0.70,
        max_abs_net_exposure=0.60,
        max_annualized_volatility=0.01,
    )
    result = evaluate_portfolio_risk_limits(
        [0.60, 0.60],
        covariance(columns, [0.04, 0.04]),
        limits,
    )
    assert result["approved"] is False
    assert result["breaches"] == [
        "max_position_weight",
        "max_gross_exposure",
        "max_abs_net_exposure",
        "max_annualized_volatility",
    ]
    assert result["position_weights"] == {"A": 0.60, "B": 0.60}


def test_net_exposure_uses_absolute_value_for_limit():
    columns = pd.Index(["A", "B"])
    limits = PortfolioRiskLimits(max_abs_net_exposure=0.20)
    result = evaluate_portfolio_risk_limits(
        [-0.70, 0.40],
        covariance(columns, [0.01, 0.01]),
        limits,
    )
    assert result["approved"] is False
    assert result["net_exposure"] == pytest.approx(-0.30)
    assert result["breaches"] == ["max_abs_net_exposure"]


def test_var_limit_requires_daily_covariance_and_uses_confidence():
    columns = pd.Index(["A", "B"])
    limits = PortfolioRiskLimits(max_daily_var_fraction=0.02, var_confidence=0.95)
    daily = covariance(columns, [0.0001, 0.0001])
    result = evaluate_portfolio_risk_limits(
        [0.5, 0.5],
        covariance(columns, [0.0252, 0.0252]),
        limits,
        covariance_daily=daily,
    )
    assert result["daily_var_fraction"] == pytest.approx(
        1.6448536269514722 * np.sqrt(0.00005), rel=1e-9
    )
    assert result["approved"] is True


@pytest.mark.parametrize(
    "weights,covariance_frame",
    [
        ([0.5, np.nan], covariance(pd.Index(["A", "B"]), [0.01, 0.01])),
        ([0.5], covariance(pd.Index(["A", "B"]), [0.01, 0.01])),
        ([0.5, 0.5], pd.DataFrame([[0.01, 0.02], [0.0, 0.01]], columns=["A", "B"], index=["A", "B"])),
        ([0.5, 0.5], pd.DataFrame([[0.01, 0.02], [0.02, 0.01]], columns=["A", "B"], index=["A", "B"])),
    ],
)
def test_invalid_inputs_fail_closed(weights, covariance_frame):
    with pytest.raises(ValueError):
        evaluate_portfolio_risk_limits(
            weights,
            covariance_frame,
            PortfolioRiskLimits(max_gross_exposure=1.0),
        )


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        PortfolioRiskLimits(max_gross_exposure=-1)
    with pytest.raises(ValueError):
        PortfolioRiskLimits(var_confidence=0.5, max_gross_exposure=1.0)
    with pytest.raises(ValueError):
        PortfolioRiskLimits()


def test_tolerance_allows_only_small_floating_point_error():
    columns = pd.Index(["A", "B"])
    limits = PortfolioRiskLimits(max_gross_exposure=1.0, tolerance=1e-9)
    result = evaluate_portfolio_risk_limits(
        [0.5 + 1e-11, 0.5],
        covariance(columns, [0.01, 0.01]),
        limits,
    )
    assert result["approved"] is True
