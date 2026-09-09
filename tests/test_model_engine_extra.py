import numpy as np
import pandas as pd
import pytest

from backend.app.services.evaluation import classification_metrics


def test_classification_metrics_reject_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        classification_metrics(pd.Series([0, 1]), np.array([0.5]))


def test_classification_metrics_return_none_roc_auc_for_single_class():
    metrics = classification_metrics(pd.Series([1, 1]), np.array([0.6, 0.9]))
    assert metrics["roc_auc"] is None
