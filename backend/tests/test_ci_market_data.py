from __future__ import annotations

import pandas as pd

from app.services.ci_market_data import CI_SYMBOLS, load_market_history


def test_ci_fixture_is_deterministic_and_valid():
    first, first_quality = load_market_history(
        "ITUB4", source="fixture", start="2021-01-04", end="2026-09-01"
    )
    second, second_quality = load_market_history(
        "ITUB4", source="fixture", start="2021-01-04", end="2026-09-01"
    )

    pd.testing.assert_frame_equal(first, second)
    assert first_quality is not None and first_quality.valid
    assert second_quality is not None and second_quality.valid
    assert len(first) >= 1400
    assert first.index.is_unique
    assert first.index.is_monotonic_increasing


def test_ci_fixture_covers_all_ci_symbols_with_distinct_series():
    histories = [load_market_history(symbol, source="fixture")[0] for symbol in CI_SYMBOLS]

    assert len(CI_SYMBOLS) == 3
    assert all(len(frame) == 1500 for frame in histories)
    assert len({float(frame["close"].iloc[0]) for frame in histories}) == len(CI_SYMBOLS)
    assert len({float(frame["close"].iloc[-1]) for frame in histories}) == len(CI_SYMBOLS)
