from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf


@dataclass(frozen=True)
class CovarianceEstimate:
    covariance: pd.DataFrame
    method: str
    shrinkage: float | None
    periods_per_year: int | None = None


def _validated_returns(returns: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(returns, pd.DataFrame):
        raise ValueError("returns must be a pandas DataFrame")
    if returns.empty:
        raise ValueError("returns must not be empty")
    if returns.shape[1] < 2 or returns.shape[0] < 2:
        raise ValueError("returns must contain at least 2 observations and 2 assets")
    if returns.columns.duplicated().any():
        raise ValueError("return columns must be unique")
    values = returns.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("returns must contain only finite values")
    return returns.astype(float)


def _finalize(
    covariance: np.ndarray,
    columns: pd.Index,
    method: str,
    shrinkage: float | None,
    periods_per_year: int | None,
) -> CovarianceEstimate:
    covariance = np.asarray(covariance, dtype=float)
    covariance = (covariance + covariance.T) / 2.0
    if not np.isfinite(covariance).all():
        raise ValueError("estimated covariance must be finite")
    if shrinkage is not None and not 0.0 <= float(shrinkage) <= 1.0:
        raise ValueError("shrinkage must be between 0 and 1")
    if periods_per_year is not None and periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if periods_per_year is not None:
        covariance = covariance * periods_per_year
    return CovarianceEstimate(
        covariance=pd.DataFrame(covariance, index=columns, columns=columns),
        method=method,
        shrinkage=None if shrinkage is None else float(shrinkage),
        periods_per_year=periods_per_year,
    )


def estimate_covariance(
    returns: pd.DataFrame,
    method: str = "sample",
    periods_per_year: int | None = None,
) -> CovarianceEstimate:
    """Estimate sample or Ledoit-Wolf covariance without implicit repair."""
    frame = _validated_returns(returns)
    if method == "sample":
        covariance = frame.cov(ddof=1).to_numpy(dtype=float)
        return _finalize(covariance, frame.columns, "sample", None, periods_per_year)
    if method == "ledoit_wolf":
        estimator = LedoitWolf().fit(frame.to_numpy(dtype=float))
        return _finalize(
            estimator.covariance_,
            frame.columns,
            "ledoit_wolf",
            estimator.shrinkage_,
            periods_per_year,
        )
    raise ValueError("unsupported covariance method; use 'sample' or 'ledoit_wolf'")


def covariance_matrix(
    returns: pd.DataFrame,
    method: str = "sample",
    periods_per_year: int | None = None,
) -> pd.DataFrame:
    """Return only the estimated covariance matrix."""
    return estimate_covariance(returns, method, periods_per_year).covariance
