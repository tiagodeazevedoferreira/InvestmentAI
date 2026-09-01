import pandas as pd
import pytest

from app.services.market_replay import MarketReplay


def sample_data():
    index = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"], utc=True)
    return pd.DataFrame(
        {
            "open": [10, 11, 12],
            "high": [11, 12, 13],
            "low": [9, 10, 11],
            "close": [10.5, 11.5, 12.5],
            "volume": [100, 200, 300],
        },
        index=index,
    )


def test_replay_is_chronological_and_deterministic():
    replay = MarketReplay("VALE3", sample_data())
    first = list(replay)
    second = list(replay)

    assert replay.total_bars == 3
    assert [bar.timestamp for bar in first] == list(sample_data().index)
    assert first == second
    assert first[0].symbol == "VALE3"
    assert first[0].close == 10.5


def test_replay_rejects_duplicate_timestamps():
    data = sample_data().copy()
    data.index = pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-06"], utc=True)
    with pytest.raises(ValueError, match="duplicate"):
        MarketReplay("VALE3", data)


def test_replay_rejects_non_chronological_data():
    data = sample_data().iloc[::-1]
    with pytest.raises(ValueError, match="chronological"):
        MarketReplay("VALE3", data)


def test_replay_rejects_missing_columns():
    data = sample_data().drop(columns=["volume"])
    with pytest.raises(ValueError, match="missing required columns"):
        MarketReplay("VALE3", data)
