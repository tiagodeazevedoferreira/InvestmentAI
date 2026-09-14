from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.data_quality import REQUIRED_OHLCV, validate_market_data
from app.services.features import build_features
from app.services.openbb_market_data import OpenBBMarketDataProvider
from app.services.technical import indicators
from app.services.walk_forward import purged_walk_forward


def _ohlcv(size: int = 80) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=size, freq="D", tz="UTC")
    close = 100.0 + 10.0 * np.sin(2 * np.pi * np.arange(size) / 10.0)
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.full(size, 1000.0),
        },
        index=index,
    )


def test_validate_market_data_accepts_valid_canonical_ohlcv() -> None:
    report = validate_market_data("PETR4", _ohlcv())

    assert report.valid
    assert report.required_columns == REQUIRED_OHLCV
    assert report.missing_columns == ()
    assert report.duplicate_timestamps == 0
    assert report.non_monotonic_timestamps == 0
    assert report.invalid_ohlc_rows == 0
    assert report.negative_volume_rows == 0


@pytest.mark.parametrize(
    ("mutation", "field"),
    [
        (lambda df: df.drop(columns="Volume"), "missing_columns"),
        (lambda df: df.rename(index={df.index[2]: df.index[1]}), "duplicate_timestamps"),
        (lambda df: df.iloc[[0, 2, 1] + list(range(3, len(df)))].copy(), "non_monotonic_timestamps"),
        (lambda df: df.assign(Close=df["Close"].astype(object).where(df.index != df.index[2], "bad")), "null_required_values"),
        (lambda df: df.assign(Close=df["Close"].where(df.index != df.index[2], np.inf)), "nonfinite_required_values"),
        (lambda df: df.assign(High=df["Open"] - 2.0), "invalid_ohlc_rows"),
        (lambda df: df.assign(Volume=-1.0), "negative_volume_rows"),
    ],
)
def test_validate_market_data_rejects_invalid_ohlcv(mutation, field: str) -> None:
    report = validate_market_data("PETR4", mutation(_ohlcv()))

    assert not report.valid
    if field == "missing_columns":
        assert report.missing_columns == ("Volume",)
    else:
        assert getattr(report, field) > 0


def test_validate_market_data_reports_calendar_gaps_without_rejecting() -> None:
    df = _ohlcv()
    df = df.drop(df.index[[10, 11, 12, 13]])

    report = validate_market_data("PETR4", df)

    assert report.valid
    assert report.large_calendar_gaps >= 1
    assert report.max_gap_days > 4


def test_normalize_symbol_preserves_provider_symbol_contract() -> None:
    provider = OpenBBMarketDataProvider()

    assert provider.normalize_symbol(" petr4 ") == "PETR4.SA"
    assert provider.normalize_symbol("PETR4.SA") == "PETR4.SA"
    with pytest.raises(ValueError, match="Symbol is required"):
        provider.normalize_symbol("   ")


def test_adapter_normalization_is_offline_and_canonical() -> None:
    raw = _ohlcv(6).rename(columns=str.lower)
    raw.index.name = "date"

    normalized = OpenBBMarketDataProvider.normalize_historical_frame(raw)

    assert list(normalized.columns[:5]) == ["Open", "High", "Low", "Close", "Volume"]
    assert isinstance(normalized.index, pd.DatetimeIndex)
    assert normalized.index.is_monotonic_increasing
    assert normalized.index.name == "date"


def test_normalized_pipeline_passes_quality_indicators_and_features() -> None:
    df = _ohlcv(80)
    quality = validate_market_data("PETR4", df)
    technical = indicators(df)
    features, target = build_features(df, horizon=5)

    assert quality.valid
    assert {"EMA9", "EMA21", "RSI14"}.issubset(technical.columns)
    assert not features.empty
    assert len(features) == len(target)
    assert features.index.equals(target.index)


def test_purged_walk_forward_runs_deterministically_on_synthetic_data() -> None:
    df = _ohlcv(180)

    result = purged_walk_forward(
        df,
        "PETR4",
        horizon=5,
        train_size=60,
        test_size=20,
        step=20,
    )

    assert len(result.folds) >= 1
    assert all(fold.test_rows == 20 for fold in result.folds)
    assert all(pd.Timestamp(fold.train_end) < pd.Timestamp(fold.test_start) for fold in result.folds)


def test_purged_walk_forward_excludes_exact_five_bar_purge(monkeypatch) -> None:
    index = pd.date_range("2026-01-01", periods=100, freq="D", tz="UTC")
    X = pd.DataFrame(
        {
            "ema9_gap": np.tile([-0.1, 0.1], 50),
            "ema21_gap": np.zeros(100),
            "ema_spread": np.tile([-0.1, 0.1], 50),
            "rsi_centered": np.tile([-0.2, 0.2], 50),
            "bb_position": np.tile([0.2, 0.8], 50),
            "bb_width": np.full(100, 0.1),
            "return_1d": np.tile([-0.01, 0.01], 50),
            "return_5d": np.tile([-0.02, 0.02], 50),
            "volatility_20d": np.full(100, 0.02),
            "volume_change": np.tile([-0.01, 0.01], 50),
        },
        index=index,
    )
    y = pd.Series(np.tile([0, 1], 50), index=index, name="target")

    monkeypatch.setattr("app.services.walk_forward.build_features", lambda df, horizon: (X, y))

    result = purged_walk_forward(
        pd.DataFrame(index=index),
        "SYNTH",
        horizon=5,
        train_size=20,
        test_size=10,
        step=10,
    )

    first = result.folds[0]
    assert first.train_start == str(index[0])
    assert first.train_end == str(index[19])
    assert first.test_start == str(index[25])
    assert first.test_end == str(index[34])
    assert pd.Timestamp(first.train_end) < index[20]
    assert index[24] < pd.Timestamp(first.test_start)
