import pandas as pd

from scripts.run_b3_backtest import ema_cross_signal


def test_ema_cross_signal_is_chronological_and_discrete():
    index = pd.date_range("2026-01-01", periods=30, freq="D", tz="UTC")
    close = pd.Series([100 + (i if i < 15 else 30 - i) for i in range(30)], index=index)
    frame = pd.DataFrame({"close": close})

    signals = ema_cross_signal(frame)

    assert signals.index.equals(index)
    assert set(signals.unique()).issubset({-1, 0, 1})
    assert signals.iloc[0] == 0
