from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_position_weight: float | None = None
    max_gross_exposure: float | None = None
    max_abs_net_exposure: float | None = None
    max_annualized_volatility: float | None = None
    max_daily_var_fraction: float | None = None
    var_confidence: float = 0.95
    tolerance: float = 1e-10

    def __post_init__(self) -> None:
        for name in (
            "max_position_weight",
            "max_gross_exposure",
            "max_abs_net_exposure",
            "max_annualized_volatility",
            "max_daily_var_fraction",
            "tolerance",
        ):
            value = getattr(self, name)
            if value is not None and (not math.isfinite(float(value)) or float(value) < 0):
                raise ValueError(f"{name} must be finite and non-negative")
        if not math.isfinite(float(self.var_confidence)) or not 0.5 < float(self.var_confidence) < 1:
            raise ValueError("var_confidence must be between 0.5 and 1")
        if self.tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        if all(
            value is None
            for value in (
                self.max_position_weight,
                self.max_gross_exposure,
                self.max_abs_net_exposure,
                self.max_annualized_volatility,
                self.max_daily_var_fraction,
            )
        ):
            raise ValueError("at least one portfolio risk limit is required")


def _validated_weights(weights, columns: pd.Index) -> np.ndarray:
    values = np.asarray(weights, dtype=float)
    if values.ndim != 1 or len(values) != len(columns):
        raise ValueError("weights must match covariance asset count")
    if not np.isfinite(values).all():
        raise ValueError("weights must be finite")
    return values


def _validated_covariance(covariance: pd.DataFrame, columns: pd.Index) -> np.ndarray:
    if not isinstance(covariance, pd.DataFrame):
        raise ValueError("covariance must be a pandas DataFrame")
    if covariance.shape != (len(columns), len(columns)):
        raise ValueError("covariance dimensions do not match weights")
    if covariance.index.tolist() != columns.tolist() or covariance.columns.tolist() != columns.tolist():
        raise ValueError("covariance labels must match asset labels and order")
    if covariance.index.duplicated().any() or covariance.columns.duplicated().any():
        raise ValueError("covariance labels must be unique")
    matrix = covariance.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("covariance must contain only finite values")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-10):
        raise ValueError("covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues.min(initial=0.0) < -1e-10:
        raise ValueError("covariance must be positive semidefinite")
    return matrix


def _breach(value: float, limit: float | None, tolerance: float) -> bool:
    return limit is not None and value > float(limit) + tolerance


def evaluate_portfolio_risk_limits(
    weights,
    covariance_annualized: pd.DataFrame,
    limits: PortfolioRiskLimits,
    *,
    covariance_daily: pd.DataFrame | None = None,
    portfolio_value: float | None = None,
) -> dict:
    columns = covariance_annualized.columns
    w = _validated_weights(weights, columns)
    annual = _validated_covariance(covariance_annualized, columns)

    if portfolio_value is not None and (
        not math.isfinite(float(portfolio_value)) or float(portfolio_value) <= 0
    ):
        raise ValueError("portfolio_value must be positive and finite")

    position_weights = np.abs(w)
    gross_exposure = float(position_weights.sum())
    net_exposure = float(w.sum())
    annualized_volatility = float(np.sqrt(max(w @ annual @ w, 0.0)))

    daily_var_fraction = None
    if limits.max_daily_var_fraction is not None:
        if covariance_daily is None:
            raise ValueError("covariance_daily is required for the configured VaR limit")
        daily = _validated_covariance(covariance_daily, columns)
        daily_volatility = float(np.sqrt(max(w @ daily @ w, 0.0)))
        daily_var_fraction = float(norm.ppf(limits.var_confidence) * daily_volatility)

    breaches: list[str] = []
    if limits.max_position_weight is not None:
        if position_weights.max(initial=0.0) > limits.max_position_weight + limits.tolerance:
            breaches.append("max_position_weight")
    if _breach(gross_exposure, limits.max_gross_exposure, limits.tolerance):
        breaches.append("max_gross_exposure")
    if _breach(abs(net_exposure), limits.max_abs_net_exposure, limits.tolerance):
        breaches.append("max_abs_net_exposure")
    if _breach(annualized_volatility, limits.max_annualized_volatility, limits.tolerance):
        breaches.append("max_annualized_volatility")
    if daily_var_fraction is not None and _breach(
        daily_var_fraction, limits.max_daily_var_fraction, limits.tolerance
    ):
        breaches.append("max_daily_var_fraction")

    return {
        "approved": not breaches,
        "breaches": breaches,
        "position_weights": {
            str(label): float(value) for label, value in zip(columns, position_weights)
        },
        "gross_exposure": gross_exposure,
        "net_exposure": net_exposure,
        "annualized_volatility": annualized_volatility,
        "daily_var_fraction": daily_var_fraction,
        "portfolio_value": None if portfolio_value is None else float(portfolio_value),
    }
