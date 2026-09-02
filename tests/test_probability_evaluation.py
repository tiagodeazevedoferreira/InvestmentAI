import numpy as np
import pytest

from backend.app.services.probability_evaluation import paired_fold_summary


def test_paired_summary_uses_candidate_minus_baseline():
    result = paired_fold_summary(
        [0.30, 0.25, 0.20, 0.35],
        [0.25, 0.27, 0.18, 0.30],
        metric="brier",
        comparison="selected_vs_raw",
        bootstrap_iterations=1000,
    )
    assert result.n == 4
    assert result.mean_delta == pytest.approx((-0.05 + 0.02 - 0.02 - 0.05) / 4)
    assert result.win_rate == pytest.approx(0.75)
    assert result.bootstrap_ci_low <= result.mean_delta <= result.bootstrap_ci_high


def test_bootstrap_is_deterministic_for_fixed_seed():
    kwargs = dict(metric="ece", comparison="selected_vs_calibrated", bootstrap_iterations=1000, seed=7)
    first = paired_fold_summary([0.10, 0.20, 0.15], [0.08, 0.21, 0.12], **kwargs)
    second = paired_fold_summary([0.10, 0.20, 0.15], [0.08, 0.21, 0.12], **kwargs)
    assert first == second


def test_invalid_paired_inputs_are_rejected():
    with pytest.raises(ValueError):
        paired_fold_summary([0.1], [0.2], metric="brier", comparison="x")
    with pytest.raises(ValueError):
        paired_fold_summary([0.1, np.nan], [0.2, 0.3], metric="brier", comparison="x")
    with pytest.raises(ValueError):
        paired_fold_summary([0.1, 0.2], [0.2, 0.3], metric="brier", comparison="x", bootstrap_iterations=10)
