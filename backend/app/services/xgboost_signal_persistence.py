from __future__ import annotations

import numpy as np
import pandas as pd


def probabilities_to_persistent_signals(
    probabilities: pd.Series,
    *,
    entry_threshold: float = 0.60,
    exit_threshold: float | None = None,
    confirmation_bars: int = 1,
) -> pd.Series:
    """Convert OOS probabilities into long-only signals with persistence/hysteresis.

    The state changes to long only after ``confirmation_bars`` consecutive
    observations at or above the entry threshold. When an exit threshold is
    supplied, an existing long position is closed only after the same number
    of consecutive observations below that threshold. With no exit threshold,
    the entry threshold is also used for exit.

    This function does not alter probabilities or retrain a model; it is an
    execution-policy transformation over an immutable OOS probability series.
    """
    if not isinstance(probabilities, pd.Series):
        raise ValueError("probabilities must be a pandas Series")
    if not probabilities.index.is_unique:
        raise ValueError("probabilities index must be unique")
    if not probabilities.index.is_monotonic_increasing:
        raise ValueError("probabilities index must be chronological")
    if not 0.0 <= entry_threshold <= 1.0:
        raise ValueError("entry_threshold must be between 0 and 1")
    if exit_threshold is None:
        exit_threshold = entry_threshold
    if not 0.0 <= exit_threshold <= 1.0:
        raise ValueError("exit_threshold must be between 0 and 1")
    if not isinstance(confirmation_bars, int) or isinstance(confirmation_bars, bool) or confirmation_bars < 1:
        raise ValueError("confirmation_bars must be a positive integer")

    values = pd.to_numeric(probabilities, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(values).all() or not ((values >= 0.0) & (values <= 1.0)).all():
        raise ValueError("probabilities must be finite values in [0, 1]")

    state = -1
    pending_entry = 0
    pending_exit = 0
    signals: list[int] = []

    for probability in values:
        if state == -1:
            pending_exit = 0
            if probability >= entry_threshold:
                pending_entry += 1
            else:
                pending_entry = 0
            if pending_entry >= confirmation_bars:
                state = 1
                pending_entry = 0
        else:
            pending_entry = 0
            if probability < exit_threshold:
                pending_exit += 1
            else:
                pending_exit = 0
            if pending_exit >= confirmation_bars:
                state = -1
                pending_exit = 0
        signals.append(state)

    return pd.Series(signals, index=probabilities.index, name="signal")
