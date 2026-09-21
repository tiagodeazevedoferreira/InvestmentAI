from __future__ import annotations

import pandas as pd

from scripts.run_xgboost_oos_economic_report import _buy_and_hold_return, _oos_replay_window


def test_benchmark_uses_the_exact_replay_window() -> None:
    index = pd.date_range("2025-01-01", periods=8, freq="D", tz="UTC")
    history = pd.DataFrame(
        {"close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 110.0, 120.0]},
        index=index,
    )
    probabilities = pd.Series(
        [0.7, 0.4, 0.8],
        index=index[[2, 4, 5]],
        name="probability",
    )

    window = _oos_replay_window(history, probabilities)

    assert window.index[0] == index[2]
    assert window.index[-1] == index[6]
    assert len(window) == 5
    assert _buy_and_hold_return(window, 100_000.0) == 100_000.0 * (110.0 / 102.0)
