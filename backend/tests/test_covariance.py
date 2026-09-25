import numpy as np
import pandas as pd
import pytest

from app.services.covariance import estimate_covariance


@pytest.fixture
def returns():
    return pd.DataFrame(
        {
            "PETR4": [0.01, -0.02, 0.015, 0.004, -0.006, 0.012],
            "VALE3": [0.02, -0.01, 0.011, 0.006, -0.004, 0.009],
            "ITUB4": [0.005, -0.003, 0.008, 0.002, -0.001, 0.007],
        }
    )


def test_sample_covariance_preserves_labels_and_symmetry(returns):
    estimate = estimate_covariance(returns, method="sample")
    assert list(estimate.covariance.columns) == ["PETR4", "VALE3", "ITUB4"]
    assert estimate.covariance.index.tolist() == estimate.covariance.columns.tolist()
    assert np.allclose(estimate.covariance, estimate.covariance.T)
    assert np.isfinite(estimate.covariance.to_numpy()).all()
    assert estimate.shrinkage is None


def test_ledoit_wolf_returns_finite_psd_covariance(returns):
    estimate = estimate_covariance(returns, method="ledoit_wolf")
    matrix = estimate.covariance.to_numpy()
    eigenvalues = np.linalg.eigvalsh(matrix)
    assert np.isfinite(matrix).all()
    assert np.allclose(matrix, matrix.T)
    assert eigenvalues.min() >= -1e-12
    assert 0.0 <= estimate.shrinkage <= 1.0


def test_annualization_is_explicit(returns):
    daily = estimate_covariance(returns, method="ledoit_wolf")
    annual = estimate_covariance(returns, method="ledoit_wolf", periods_per_year=252)
    assert np.allclose(annual.covariance.to_numpy(), daily.covariance.to_numpy() * 252)
    assert annual.periods_per_year == 252


@pytest.mark.parametrize(
    "frame",
    [
        pd.DataFrame(),
        pd.DataFrame({"A": [1.0, 2.0]}),
        pd.DataFrame({"A": [1.0, np.nan], "B": [2.0, 3.0]}),
    ],
)
def test_invalid_returns_fail_closed(frame):
    with pytest.raises(ValueError):
        estimate_covariance(frame)


def test_duplicate_columns_fail_closed():
    frame = pd.DataFrame([[0.1, 0.2], [0.2, 0.1]], columns=["A", "A"])
    with pytest.raises(ValueError, match="unique"):
        estimate_covariance(frame)


def test_invalid_method_and_periods_fail_closed(returns):
    with pytest.raises(ValueError, match="unsupported"):
        estimate_covariance(returns, method="oas")
    with pytest.raises(ValueError, match="positive"):
        estimate_covariance(returns, periods_per_year=0)
