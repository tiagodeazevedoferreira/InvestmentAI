import pandas as pd

from scripts.run_b3_backtest import ema_cross_signal


def test_ema_signal_does_not_change_when_future_prices_change():
    index = pd.date_range("2026-01-01", periods=40, freq="D", tz="UTC")
    base = [100 + i * 0.2 for i in range(40)]
    altered = base[:20] + [300 + i * 10 for i in range(20)]

    first = ema_cross_signal(pd.DataFrame({"close": base}, index=index))
    second = ema_cross_signal(pd.DataFrame({"close": altered}, index=index))

    assert first.iloc[:20].equals(second.iloc[:20])


def test_ema_signal_uses_previous_bar_for_cross_detection():
    index = pd.date_range("2026-01-01", periods=5, freq="D", tz="UTC")
    frame = pd.DataFrame({"close": [100.0, 100.0, 100.0, 120.0, 130.0]}, index=index)
    signals = ema_cross_signal(frame)

    assert signals.index.equals(index)
    assert set(signals.unique()).issubset({-1, 0, 1})
    assert signals.iloc[0] == 0
