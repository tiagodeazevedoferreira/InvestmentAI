import numpy as np
import pandas as pd
import pytest

from app.services.lstm import LSTMConfig, chronological_sequence_split, make_sequences, train_lstm


def _frame(rows: int = 30) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "f1": np.arange(rows, dtype=float),
            "f2": np.arange(rows, dtype=float) / rows,
            "target": (np.arange(rows) % 2).astype(float),
        }
    )


def test_make_sequences_is_causal_and_preserves_order():
    x, y = make_sequences(_frame(), ["f1", "f2"], "target", sequence_length=5)
    assert x.shape == (25, 5, 2)
    assert y.shape == (25,)
    assert x[0, 0, 0] == 0
    assert x[0, -1, 0] == 4
    assert y[0] == 1
    assert x[-1, -1, 0] == 29


def test_chronological_split_has_no_shuffle():
    x, y = make_sequences(_frame(40), ["f1", "f2"], "target", 5)
    (train_x, train_y), (val_x, val_y), (test_x, test_y) = chronological_sequence_split(x, y)
    assert train_x[0, 0, 0] < val_x[0, 0, 0] < test_x[0, 0, 0]
    assert len(train_x) == len(train_y)
    assert len(val_x) == len(val_y)
    assert len(test_x) == len(test_y)


def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError):
        make_sequences(_frame(10), ["missing"], "target", 5)
    with pytest.raises(ValueError):
        LSTMConfig(sequence_length=1)
    with pytest.raises(ValueError):
        chronological_sequence_split(np.zeros((2, 3, 1)), np.zeros(3))


def test_training_requires_pytorch_or_returns_structured_result():
    x, y = make_sequences(_frame(40), ["f1", "f2"], "target", 5)
    (train_x, train_y), (val_x, val_y), _ = chronological_sequence_split(x, y)
    try:
        result = train_lstm(
            train_x,
            train_y,
            val_x,
            val_y,
            LSTMConfig(epochs=1, hidden_size=4, batch_size=8),
        )
    except RuntimeError as exc:
        assert "PyTorch" in str(exc)
    else:
        assert 0.0 <= result["validation_accuracy"] <= 1.0
        assert result["epochs"] == 1
